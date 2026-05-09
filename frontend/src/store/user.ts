import {defineStore} from "pinia";

export const useUserstore = defineStore(
    'user',
    {
        state() {
            return {
                userName: localStorage.getItem('userName') || '',
                token: localStorage.getItem('token') || '',
            }
        },
        actions: {
            setUser(userName: string, token: string) {
                this.userName = userName
                this.token = token
                localStorage.setItem('userName', userName)
                localStorage.setItem('token', token)
            },
            clearUser() {
                this.userName = ''
                this.token = ''
                localStorage.removeItem('userName')
                localStorage.removeItem('token')
            },
        },
    }
)
