<template>
	<div class="valid-feedback">
		{{affirm}}
	</div>
	<div class="invalid-feedback">
		{{invalid}}
	</div>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";

export default defineComponent({
	props: {
		invalid: {type: String, default: "Please fill this out."},
	},
	setup() {
		const affirmativePhrases = ["Looks good!", "Awesome!", "Nice!", "Good job!"];
		let affirm = ref(affirmativePhrases[Math.floor(Math.random() * affirmativePhrases.length)]);

		return { affirm };
	}
});
</script>