<template>
<div class="dropdown">
	<k-button v-if="type === 'button'" ref="dropdownEl" data-bs-toggle="dropdown" :color="btnColor" :size="btnSize" :variant="btnVariant" id="navbarDropdown">
		{{ text }}
	</k-button>
	<a v-else id="navbarDropdown" ref="dropdownEl" href="#" class="nav-link px-0" role="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
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
		type: {type: String, default: "button", validator(t: string) {return ["button", "custom"].indexOf(t) !== -1}},
		text: {type: String, default: ""},
		btnColor: {type: String, default: "primary"},
		btnSize: {type: String, default: ""},
		btnVariant: {type: String, default: "outline"}
	},
	setup(_props, {emit}) {
		const dropdownEl: Ref<HTMLElement | null> = ref(null);
		let dropDown: any = null;
		function setupDD(el: HTMLElement) {
			["show", "shown", "hide", "hidden"].forEach((e) => {
				el.addEventListener(`${e}.bs.dropdown`, () => {
					emit(e);
				});
			});
			el.addEventListener("click", () => {
				if (el.parentNode?.querySelector(".dropdown-menu")?.classList.contains("show"))
					dropDown.hide();
				else dropDown.show();
			})
		}
		onMounted(() => {
			// If the trigger type isn't button
			if(dropdownEl.value != null) {
				dropDown = new Dropdown(dropdownEl.value as HTMLElement);
				setupDD(dropdownEl.value as HTMLElement);
			}
			// To handle waiting for button component to load
			else {
				watch(dropdownEl, el => {
					dropDown = new Dropdown(el as HTMLElement);
					setupDD(el as HTMLElement);
				});
			}
		});
		return { dropdownEl };
	}
});
</script>

<style scoped></style>