<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup
import { RouterView, RouterLink } from "vue-router";
import Button from "primevue/button";
import Sidebar from "primevue/sidebar";
import Menu from "primevue/menu";
import {ref} from "vue";
import "primevue/resources/themes/lara-dark-teal/theme.css";
import "primevue/resources/primevue.min.css";
import "primeicons/primeicons.css";
import "primeflex/primeflex.css";

const visibleNav = ref(false);
function toggleNav() {
	visibleNav.value = !visibleNav.value;
}

const collapsedItems = [{
	label: "",
	icon: "pi pi-home",
	to: "/"
}, {
	label: "",
	icon: "pi pi-at",
	to: "/about"
	//command: () => {
		//this.$toast.add({ severity: "warn", summary: "Delete", detail: "Data Deleted", life: 3000});
	//}
}, {
	label: "",
	icon: "pi pi-upload",
	to: "/upload"
}, {
	label: "",
	icon: "pi pi-search",
	to: "/search"
}, {
	label: "",
	icon: "pi pi-users",
	to: "/collections"
}, {
	label: "",
	icon: "pi pi-clone",
	to: "/my-collections"
}];

const fullItems = [{
	label: "Home",
	icon: "pi pi-home",
	to: "/"
}, {
	label: "About",
	icon: "pi pi-at",
	to: "/about"
}, {
	label: "Upload",
	icon: "pi pi-upload",
	to: "/upload"
}, {
	label: "Search",
	icon: "pi pi-search",
	to: "/search"
}, {
	label: "Public Collections",
	icon: "pi pi-users",
	to: "/collections"
}, {
	label: "My Collections",
	icon: "pi pi-clone",
	to: "/my-collections"
}];
</script>

<template>
	<div id="app-menus">
		<Button icon="pi pi-chevron-right" @click="toggleNav"></Button>
		<Menu :model="collapsedItems" id="collapsedMenu"></Menu>
		<Sidebar position="left" v-model:visible="visibleNav" class="p-sidebar-sm">
			<Menu :model="fullItems"></Menu>
		</Sidebar>
	</div>
	<div id="app-body">
		<!-- <img alt="Vue logo" src="./assets/logo.png" />
		<br /> -->
		<!-- <div class="router-links-container">
			<router-link to="/">
				<Button>Home</Button>
			</router-link> | 
			<router-link to="/about">
				<Button>About</Button>
			</router-link>
		</div> -->
		<router-view />
	</div>
</template>

<style>
.router-links-container a {
	color: var(--text-color) !important;
	text-decoration: none !important;
}
body {
	background-color: var(--surface-a);
    font-family: var(--font-family);
	color: var(--text-color);
}
#collapsedMenu {
	width: 3rem;
	margin-top: 1rem;
}
#collapsedMenu a {
	padding-left: 1rem;
	text-align: center;
}
#app-menus {
	float: left;
	width: 3rem;
}
#app-body {
	text-align: center;
	width: calc(100% - 3rem);
	float: right;
}
.p-sidebar-left.p-sidebar-sm {
	width: 15rem;
}
</style>
