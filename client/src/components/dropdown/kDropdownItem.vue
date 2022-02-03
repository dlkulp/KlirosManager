<template>
<a v-if="link" class="dropdown-item" :href="link">
	<slot />
</a>
<a v-else class="dropdown-item">
	<slot />
</a>
</template>

<script lang="ts">
import { toRefs, defineComponent } from "vue";

export default defineComponent({
	props: {
		link: {type: String, default: ""}
	},
	setup(props: Props) {
		const { link } = toRefs(props);

		return { link };
	}
});

interface Props {
	link: string;
}
</script>