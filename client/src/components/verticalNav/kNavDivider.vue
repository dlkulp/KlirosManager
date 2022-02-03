<template>
	<div class="row mt-3 mb-2">
		<div v-if="label" class="col-auto navbar-vertical-label">
			{{label}}
		</div>
		<div class="col ps-0">
			<hr class="mb-0 navbar-vertical-divider">
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

export default defineComponent({
	props: {
		label: {type: String}
	},
	setup() {}
});
</script>