<script lang="ts">
import { ref, toRefs, watch, defineComponent } from "vue";

export default defineComponent({
	props: {
		type: {type: String, default: "badge", validator(t: string) {return ["badge", "pill"].indexOf(t) !== -1}},
		color: {type: String, default: "primary", validator(c: string) {return ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark", "default"].indexOf(c) !== -1}}
	},
	setup(props: Props) {
		const { color, type } = toRefs(props);
		
		// Set initial class string and watch for updates
		const badgeClasses = ref(setBadgeClass(type.value, color.value));
		watch([color, type], ([newColor, newType]) => {
			badgeClasses.value = setBadgeClass(newColor as string, newType as string);
		});

		function setBadgeClass(type: string, color: string) {
			const _size = type == "pill" ? "rounded-pill" : "";
			const _color = `bg-${color}`;

			return `badge ${_color} ${_size}`;
		}

		// In Composition API, these are the reactive parts used on the page
		return { badgeClasses, type: <any>type };
	}
});

interface Props {
	type: string;
	color: string;
}
</script>

<template>
<span :class="badgeClasses"><slot /></span>
</template>