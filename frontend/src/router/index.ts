import {createRouter, createWebHistory} from "vue-router";

import Login from '@/pages/Login.vue';
import Index from "@/pages/Index.vue";
import Test from "@/pages/Test.vue";
import CheckUserInfo from "@/components/CheckUserInfo.vue";
import Profile from "@/components/Profile.vue";
import AddUser from "@/components/AddUser.vue";
import Chat from "@/components/Chat.vue";
import Register from "@/pages/Register.vue";
import PaperSearch from "@/components/PaperSearch.vue";
import PaperDetail from "@/components/PaperDetail.vue";
import PaperRecommend from "@/components/PaperRecommend.vue";

const routes =
    [
        {
            path: '/',
            name: 'Login',
            component: Login
        },
        {
            path: '/register',
            name: 'Register',
            component: Register
        },
        {
            path: '/index',
            name: 'Index',
            component: Index,
            children: [
                {
                    path: '',
                    name:'IndexMain',
                    component: Profile,
                },
                {
                    path: 'checkUserInfo/:username',
                    name: 'checkUserDetail',
                    component: Profile,
                    props: true
                },
                {
                    path: 'checkUserInfo',
                    component: CheckUserInfo,
                },
                {
                    path: 'addUser',
                    component: AddUser,
                },
                {
                    path: 'chat',
                    component: Chat,
                },
                {
                    path: 'paperSearch',
                    name: 'PaperSearch',
                    component: PaperSearch,
                },
                {
                    path: 'paperDetail/:paperId',
                    name: 'PaperDetail',
                    component: PaperDetail,
                    props: true,
                },
                {
                    path: 'paperRecommend',
                    name: 'PaperRecommend',
                    component: PaperRecommend,
                },
            ]

        },
        {
            path: '/test',
            name: 'Test',
            component: Test
        }
    ];

const router = createRouter({
    history: createWebHistory(),
    routes
});

router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('token')
    if (to.path.startsWith('/index') && !token) {
        next('/')
    } else {
        next()
    }
})

export default router;
