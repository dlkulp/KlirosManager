<script setup lang="ts">
import KFileUploader from "../components/forms/kFileUploader.vue";
import {ref} from "vue";

function upload(_event: any) {
	console.log("upload")
}
function select(_event: any) {
	console.log("select");
}

const files = ref();
</script>

<template>
<h1>Upload Score</h1>
<KFileUploader :allowFileTypeValidation="true" fileTypes="application/pdf, image/*" :maxFiles="1" v-model="files" :required="true" />
</template>

<style>
.p-fileupload { 
	margin-left: .5rem;
}
</style>