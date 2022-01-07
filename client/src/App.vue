<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup
import { RouterView, RouterLink } from "vue-router";
import Button from "primevue/button";
import "primevue/resources/themes/lara-dark-teal/theme.css";
import "primevue/resources/primevue.min.css";
import "primeicons/primeicons.css";

</script>

<template>
	<img alt="Vue logo" src="./assets/logo.png" />
	<br />
	<div class="router-links-container">
		<router-link to="/">
			<Button>Home</Button>
		</router-link> | 
		<router-link to="/about">
			<Button>About</Button>
		</router-link>
	</div>
	<router-view />
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
#app {
	text-align: center;
}
</style>
