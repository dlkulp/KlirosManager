<template>
<div class="dropdown" ref="dropdownEl">
	<k-button v-if="type === 'button'" data-bs-toggle="dropdown" :color="btnColor" :size="btnSize" :variant="btnVariant" id="navbarDropdown">
		{{ text }}
	</k-button>
	<a v-else id="navbarDropdown" href="#" class="nav-link px-0" role="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
		<slot name="trigger" />
	</a>
	<div class="dropdown-menu dropdown-menu-end py-0" onclick="event.stopPropagation();" aria-labelledby="navbarDropdown">
		<slot />
	</div>
</div>
</template>

<script lang="ts">
import kButton from "../kButton.vue";
import { defineComponent, onMounted, ref, Ref, watch } from "vue";
import Dropdown from "bootstrap/js/dist/dropdown.js";

export default defineComponent({
	components: {kButton},
	props: {
		type: {type: String, default: "button", validator(t: string) {return ["button", "other"].indexOf(t) !== -1}},
		text: {type: String, default: ""},
		btnColor: {type: String, default: "primary"},
		btnSize: {type: String, default: ""},
		btnVariant: {type: String, default: "outline"}
	},
	setup() {
		const dropdownEl: Ref<HTMLElement | null> = ref(null);
		onMounted(() => {
			watch(dropdownEl, curr => {
				if (curr)
					new Dropdown(curr);
			});
		});
		return { dropdownEl };
	}
});
</script>

<style scoped></style>