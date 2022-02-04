<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup
import { RouterView, RouterLink, useRoute } from "vue-router";
import {ref, computed, reactive} from "vue";
import kPageNavigation from "./components/kPageNavigation.vue";
import kNavItem from "./components/verticalNav/kNavItem.vue";
import kDropdownItem from "./components/dropdown/kDropdownItem.vue";
import kDropdownDivider from "./components/dropdown/kDropdownDivider.vue";
import kUserNav from "./components/kUserNav.vue";
import logo from "./assets/logo.svg";
import unknownUser from "./assets/unknown_user.svg";

let url = computed(() => useRoute().name);
let brand = reactive({route:"/", image: {source: logo, width: 40, title: "Kliros"}});
let userImage = unknownUser;

const visibleNav = ref(false);
function toggleNav() {
	visibleNav.value = !visibleNav.value;
}

const routes = [{
	label: "Home",
	icon: ["fa", "house"],
	to: "/"
}, {
	label: "About",
	icon: ["fa", "at"],
	to: "/about"
}, {
	label: "Upload",
	icon: ["fa", "arrow-up-from-bracket"],
	to: "/upload"
}, {
	label: "Search",
	icon: ["fa", "magnifying-glass"],
	to: "/search"
}, {
	label: "Public Collections",
	icon: ["fa", "user-group"],
	to: "/collections"
}, {
	label: "My Collections",
	icon: ["fa", "layer-group"],
	to: "/my-collections"
}];
</script>

<template>
<kPageNavigation :brand="brand">
	<template v-slot:mainNav>
		<kNavItem v-for="route in routes" :name="route.label" :route="route.to">
			<template v-slot:icon><font-awesome-icon class="pe-2" :icon="route.icon" /></template>
		</kNavItem>
	</template>
	<template v-slot:topRight>
		<kUserNav :userImage="userImage">
			<kDropdownItem link="/buttons?profile=1">Profile &amp; account</kDropdownItem>
			<kDropdownItem link="/buttons?feedback=1">Feedback</kDropdownItem>
			<kDropdownItem link="/buttons?settings=1">Settings</kDropdownItem>
			<kDropdownDivider />
			<kDropdownItem link="/buttons?logout=1">Logout</kDropdownItem>
		</kUserNav>
	</template>
	<template v-slot:pageContent>
		<router-view />
	</template>
</kPageNavigation>
</template>

<style lang="scss">
@media (prefers-color-scheme: dark) {
.btn-outline-primary {
	color: var(--bs-primary);
	border-color: var(--bs-primary);
}
}
body {
	background-color: var(--surface-a);
    font-family: var(--font-family);
	color: var(--text-color);
	// Lenten
	--lentPrimary: #A82DE9;
	--lentPrimaryDark: #8222B5;
	
	// Vars used globally
	--primaryColor: var(--lentPrimary);
	--primaryDark: var(--lentPrimaryDark);
}
main {
	display: flex;
    flex-wrap: nowrap;
    height: -webkit-fill-available;
    height: 100vh;
    max-height: 100vh;
    overflow-x: auto;
    overflow-y: hidden;
}
</style>
