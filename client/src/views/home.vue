<script setup lang="ts">
import { ref } from "vue"
import kButton from "../components/kButton.vue";

//defineProps<{ msg: string }>()

const vis = ref(true)

const count = ref(0)
</script>

<template>
	<!-- <h1>{{ msg }}</h1> -->
	<h1>Welcome</h1>
	<p>
		Recommended IDE setup:
		<a href="https://code.visualstudio.com/" target="_blank">VSCode</a>
		+
		<a href="https://github.com/johnsoncodehk/volar" target="_blank">Volar</a>
	</p>

	<p>
		See <code>README.md</code> for more information
	</p>

	<p>
		<a href="https://vitejs.dev/guide/features.html" target="_blank">Vite Docs</a>
		|
		<a href="https://v3.vuejs.org/" target="_blank">Vue 3 Docs</a>
		|
		<a href="https://getbootstrap.com/docs/5.1/" target="_blank">Bootstrap 5 Docs</a>
	</p>

	<kButton @click="count++">count is: {{count}}</kButton>
	<p>
		Edit <code>views/home.vue</code> to test hot module replacement.
	</p>
</template>

<style scoped>
a {
	color: #42b983;
}

label {
	margin: 0 0.5em;
	font-weight: bold;
}

code {
	background-color: #eee;
	padding: 2px 4px;
	border-radius: 4px;
	color: #304455;
}
</style>
