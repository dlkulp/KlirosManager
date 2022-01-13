<script setup lang="ts">
import FileUpload from "primevue/fileupload";

function upload(event) {
	console.log("upload")
}
function select(event) {
	console.log("select");
}
</script>

<template>
<h1>Upload Score</h1>
<FileUpload name="scores" :customUpload="true" @uploader="upload" @select="select" :multiple="true">
	<template #empty>
        <p>Drag and drop files to here to upload.</p>
    </template>
</FileUpload>
</template>

<style>
.p-fileupload {
	margin-left: .5rem;
}
</style>