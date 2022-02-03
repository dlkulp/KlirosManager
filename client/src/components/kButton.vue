<template>
	<button v-if="type !== 'link'" :type="type" :disabled="disabled" :class="buttonClasses">
		<slot />
	</button>
	<a v-else :disabled="disabled" :class="buttonClasses">
		<slot />
	</a>
</template>

<script lang="ts">
import { ref, toRefs, watch, defineComponent } from "vue";

export default defineComponent({
	props: {
		type: {type: String, default: "button", validator(t: string) {return ["button", "submit", "link"].indexOf(t) !== -1}},
		color: {type: String, default: "primary", validator(c: string) {return ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark", "default"].indexOf(c) !== -1}},
		size: {type: String, default: "", validator(s: string) {return ["", "lg", "sm"].indexOf(s) !== -1}},
		block: {type: Boolean, default: false},
		variant: {type: String, default: "outline", validator(v: string) {return ["solid", "outline"].indexOf(v) !== -1}},
		disabled: {type: Boolean, default: false}
	},
	setup(props: Props) {
		const { color, size, block, variant, disabled, type } = toRefs(props);
		
		// Set initial class string and watch for updates
		const buttonClasses = ref(setButtonClass(color.value, variant.value, size.value, block.value));
		watch([color, variant, size, block], ([newColor, newVariant, newSize, newBlock]) => {
			buttonClasses.value = setButtonClass(newColor as string, newVariant as string, newSize as string, newBlock as boolean);
		});

		function setButtonClass(color: string, variant: string, size: string, block: boolean) {
			const _size = size ? `btn-${size}` : "";
			const _block = block ? "btn-block" : "";
			const _variant = variant !== "solid" ? `-${variant}` : "";
			const _color = `btn${_variant}-${color}`;

			return `btn ${_color} ${_size} ${_block}`;
		}

		// In Composition API, these are the reactive parts used on the page
		return { disabled, buttonClasses, type: <any>type };
	}
});

interface Props {
	type: string;
	color: string;
	size: string;
	block: boolean;
	variant: string;
	disabled: boolean;
}
</script>