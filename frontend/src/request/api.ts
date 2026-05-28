import instance from '@/request/http'
import loginInstance from '@/request/http_login'

interface ReqLogin {
    username: string
    password: string
}
interface ResLogin {
    access_token: string
}

interface ReqRegister {
    username: string
    email: string
    first_name: string
    last_name: string
    password: string
}

type Res<T> = Promise<ItypeAPI<T>>;
interface ItypeAPI<T> {
    success: string | null
    result: T
    msg: string | null
    message: string
    code: number
    user: User
    users: User[]
    total_users: number
    total_pages: number
}

interface User {
    username: string
    email: string
    first_name: string
    last_name: string
    is_active: boolean
    is_superuser: boolean
}

interface UserList {
    total: number
    users: User[]
}

interface LLMRequest {
    prompt: string
}

interface LLMResponse {
    response: string
}

export const TestHello = (): Res<null> =>
    instance.get('/api/hello');

export const LoginApi = (data: ReqLogin): Promise<ResLogin> =>
    loginInstance.post('/api/token', data);

export const RegisterApi = (data: ReqRegister): Promise<User> =>
    instance.post('/api/users/', data);

export const LogoutApi = (): Res<null> =>
    instance.get('/api/logout');

export const GetUserInfoByUserName = (params: { userName: string }): Promise<User> =>
    instance.get(`/api/users/name/${params.userName}`);

export const GetUserInfoList = (params: { skip: number, limit: number }): Promise<UserList> =>
    instance.get(`/api/users/`, {params});

export const ChatWithLLM = (data: LLMRequest): Promise<LLMResponse> =>
    instance.post(`/api/chat`, data);

interface ChatMsg {
    role: string
    content: string
}

export async function ChatStream(
    messages: ChatMsg[],
    onChunk: (text: string) => void,
    onDone: () => void,
) {
    const token = localStorage.getItem('token') || ''
    const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({messages}),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
        const {done, value} = await reader.read()
        if (done) break
        buffer += decoder.decode(value, {stream: true})
        const lines = buffer.split('\n')
        buffer = lines.pop()!
        for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed) continue
            if (trimmed.startsWith('data: ')) {
                const data = trimmed.slice(6)
                if (data === '[DONE]') {
                    onDone()
                    return
                }
                try {
                    const parsed = JSON.parse(data)
                    const content = parsed.choices?.[0]?.delta?.content
                    if (content) onChunk(content)
                } catch {
                    // skip non-JSON lines
                }
            }
        }
    }
    onDone()
}

interface PaperBrief {
    id: number
    title: string
    authors: string
    venue: string
    year: number
    keywords: string
    url: string
}

interface PaperDetail {
    id: number
    title: string
    abstract: string
    authors: string
    venue: string
    year: number
    keywords: string
    url: string
    created_at: string | null
}

interface SearchReq {
    query: string
    page: number
    page_size: number
    use_rerank?: boolean
    recall_k?: number
    rerank_provider?: string
}

interface SearchRes {
    total: number
    papers: PaperBrief[]
}

interface RecommendRes {
    papers: PaperBrief[]
}

interface SearchHistoryItem {
    id: number
    query: string
    searched_at: string | null
}

interface SearchHistoryRes {
    items: SearchHistoryItem[]
}

export const SearchPapers = (data: SearchReq): Promise<SearchRes> =>
    instance.post(`/api/search`, data);

export const GetPaperDetail = (paperId: number): Promise<PaperDetail> =>
    instance.get(`/api/papers/${paperId}`);

export const RecordClick = (paperId: number): Promise<any> =>
    instance.post(`/api/click`, { paper_id: paperId });

export const GetRecommendations = (): Promise<RecommendRes> =>
    instance.get(`/api/recommend`);

export const GetSearchHistory = (): Promise<SearchHistoryRes> =>
    instance.get(`/api/search/history`);
