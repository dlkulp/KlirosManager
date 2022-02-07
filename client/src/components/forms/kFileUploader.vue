<template>
	<k-input-group class="fileUploaderGroup" :label="label" :invalidText="invalidText">
		<input type="checkbox" style="display:none" :checked="uploadedFiles.length > 0" :required="required" :disabled="disabled" />
		<file-pond
			:name="name"
			:label-idle="prompt"
			:allow-multiple="allowMultiple"
			:server="server"
			:accepted-file-types="fileTypes"
			:allowFileTypeValidation="allowFileTypeValidation"
			:allowImagePreview="previewImages"
			:max-files="maxFiles"
			:storeAsFile="true"
			:credits="''"
			:disabled="disabled"
			:required="required"
			:files="files"
			v-on:initfile="initfile"
			v-on:processfile="processfile"
			v-on:removefile="removefile"
			v-on:updatefiles="updateFiles" />
	</k-input-group>
</template>

<script lang="ts">
// Import Vue FilePond
import vueFilePond from "vue-filepond";
// Import FilePond styles
import "filepond/dist/filepond.min.css";
import "filepond-plugin-image-preview/dist/filepond-plugin-image-preview.min.css";
import "filepond-plugin-media-preview/dist/filepond-plugin-media-preview.min.css";

// Import FilePond plugins

// Import preview and file type validation plugins
import FilePondPluginFileValidateType from "filepond-plugin-file-validate-type";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import FilePondPluginMediaPreview from "filepond-plugin-media-preview";

import { defineComponent, PropType, Ref, ref, toRefs, watch } from "vue";
import kInputGroup from "./kInputGroup.vue";

// Create component
const FilePond: any = vueFilePond(
	FilePondPluginFileValidateType,
	FilePondPluginImagePreview,
	FilePondPluginMediaPreview
);

export default defineComponent({
	components: { FilePond, kInputGroup },
	props: {
		label: {type: String, default: ""},
		name: {type: String, default: ""},
		prompt: {type: String},
		allowMultiple: {type: Boolean, default: true},
		server: {type: String},
		allowFileTypeValidation: {type: Boolean, default: false},
		fileTypes: {type: String},
		maxFiles: {type: Number},
		previewImages: {type: Boolean, default: true},
		invalidText: {type: String, default: "Please select files"},
		disabled: {type: Boolean, default: false},
		required: {type: Boolean, default: false},
		modelValue: {type: Array as PropType<string[]>, default: []}
	},
	setup(props, { emit }) {
		const { modelValue, label, server } = toRefs(props);
		const files = ref(modelValue?.value);
		const uploadedFiles: Ref<string[]> = ref([]);

		function processfile (error: any, file: any) {
			if (!error) {
				console.log("FilePond succesfully processed file " + file.filename);
				uploadedFiles.value.push(file.filename);
				emit("processfile", file);
			}
		}

		function initfile (file: any) {
			if (!server)
				uploadedFiles.value.push(file.filename);
		}

		function removefile (_error: any, file: any) {
			console.log("FilePond deleted file " + file.filename);
			//const index = files.value.indexOf(file.filename);
			let idx = uploadedFiles.value.indexOf(file.filename);
			if (idx > -1) uploadedFiles.value.splice(idx, 1);
		}

		function updateFiles (newFiles: string[]) {
			files.value = newFiles;
			emit("updateFiles", newFiles);
		}

		// Bubble changes up to original context
		watch(files, newVal => emit("update:modelValue", newVal));
		watch(modelValue, newVal => files.value = newVal);

		const id = label.value.replace(/\s+/g, '') || window.crypto.getRandomValues(new Uint32Array(1))[0].toString(16);
		return { id, files, uploadedFiles, processfile, removefile, initfile, updateFiles };
	}
});

</script>

<style lang="scss">
.fileUploaderGroup {
	--backgroundColor: #fff;
	--borderColor: #ced4da;
	--previewBackgroundColor: #e9ecef;
	--overlayGradient: rgba(145, 145, 145, 0.85);
	--overlayColor: #000;
}

@media (prefers-color-scheme: dark) {
	.fileUploaderGroup {
		--backgroundColor: #222;
		--borderColor: #515151;
		--previewBackgroundColor: #343a40;
		--overlayGradient: rgba(40,40,40,.85);
		--overlayColor: #fff;
	}
}

.filepond--drop-label, .filepond--drop-label label {
	color: inherit;
	cursor: pointer;
}

.filepond--panel-root {
	background-color: var(--backgroundColor) !important;
	border-radius: 0.25rem;
}

.filepond--root {
	margin-bottom: inherit;
}

.fileUploaderGroup .input-group {
	display: inherit !important;
}

.filepond--image-preview {
	background-color: var(--previewBackgroundColor);
}

.filepond--wrapper {
	background-color: var(--backgroundColor);
	border: 1px solid var(--borderColor);
	border-radius: 0.25rem !important;
	transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.filepond--image-preview-overlay-idle {
	color: var(--overlayGradient);
}

.filepond--file-info {
	color: var(--overlayColor);
}

.was-validated :valid ~ .filepond--wrapper {
	border: 1px solid var(--bs-success);
	padding-right: calc(1.5em + 0.625rem);
	padding-left: calc(1.5em + 0.625rem);
	background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2300d27a' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
	background-repeat: no-repeat;
	background-position: right calc(0.375em + 0.15625rem) center;
	background-size: calc(0.75em + 0.3125rem) calc(0.75em + 0.3125rem);
}

.was-validated :invalid ~ .filepond--wrapper {
	border: 1px solid var(--bs-danger);
	padding-right: calc(1.5em + 0.625rem);
	padding-left: calc(1.5em + 0.625rem);
	background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23e63757'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23e63757' stroke='none'/%3e%3c/svg%3e");
	background-repeat: no-repeat;
	background-position: right calc(0.375em + 0.15625rem) center;
	background-size: calc(0.75em + 0.3125rem) calc(0.75em + 0.3125rem);
}

input:disabled ~ .filepond--wrapper .filepond--panel-root {
	background-color: var(--bs-gray-200) !important;
	border-color: rgba(118, 118, 118, 0.3);
}
</style>