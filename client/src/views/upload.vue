<script setup lang="ts">
import kFileUploader from "../components/forms/kFileUploader.vue";
import kForm from "../components/forms/kForm.vue";
import kCard from "../components/cards/kCard.vue";
import kCardHeader from "../components/cards/kCardHeader.vue";
import {ref, watch, Ref} from "vue";
import { makeRequestAsync, getRandom } from "../helpers/helpers";
import grid, { GridItems } from "../components/grid.vue";

const uploaded: Ref<GridItems[]> = ref([]);
async function getUploaded() {
	let _p: any = await makeRequestAsync({ url: "/api/v1/scores/review", verb: "post"});
	_p.forEach((x: any) => x.img = {url:"",alt:"score"});
	uploaded.value = _p;
};
getUploaded();
const server = ref("/api/v1/upload");
const files = ref([]);
function processFile(newFile: any) {
	uploaded.value.push({DisplayName: newFile.filename, MetaData: {}, img: {url:"", alt:""}, id: `${getRandom(1000)}` })
}
// watch(files, (newFiles, oldFiles) => {
// 	console.log(newFiles);
// })
</script>

<template>
<h1>Uploads</h1>
<kForm class="mt-3 mb-4">
	<kFileUploader 
		:server="server" 
		:allowFileTypeValidation="true" 
		fileTypes="application/pdf, image/*" 
		v-model="files" 
		prompt="Drag & Drop or <u>Browse</u> for New Scores"
		:required="true"
		v-on:processfile="processFile" />
</kForm>
<kCard>
	<template #header><kCardHeader>My Uploads</kCardHeader></template>
	<grid :delete-items="true" v-model="uploaded"></grid>
</kCard>
</template>

<style>
.p-fileupload { 
	margin-left: .5rem;
}
</style>