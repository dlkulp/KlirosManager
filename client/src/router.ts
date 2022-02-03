import { createRouter, createWebHistory } from "vue-router";
import Home from "./views/home.vue";
import About from "./views/about.vue";
import Upload from "./views/upload.vue";
import Search from "./views/search.vue";
import Collections from "./views/collections.vue";
import MyCollections from "./views/myCollections.vue";
import Viewer from "./views/viewer.vue";

const routes = [
	{ path: "/", name: "Home", component: Home },
	{ path: "/about", name: "About", component: About },
	{ path: "/upload", name: "Upload", component: Upload },
	{ path: "/search", name: "Search", component: Search },
	{ path: "/score/:scoreId", name: "View", component: Viewer },
	{ path: "/collections", name: "Public Collections", component: Collections },
	{ path: "/my-collections", name: "My Collections", component: MyCollections }
];

export const router = createRouter({
	history: createWebHistory(),
	routes
});