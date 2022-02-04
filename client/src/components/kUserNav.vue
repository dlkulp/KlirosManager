<template>
<kDropdown type="custom" class="userNav">
	<template #trigger>
		<kAvatar :image="{src: userImage, alt: 'avatar'}" />
	</template>
	<div class="rounded-2 py-2">
		<slot />
	</div>
</kDropdown>
</template>

<script lang="ts">
import { toRefs, defineComponent } from "vue";
import kDropdown from "./dropdown/kDropdown.vue";
import kAvatar from "./kAvatar.vue";

export default defineComponent({
	components: {kAvatar, kDropdown},
	props: {
		userImage: {type: String, default:""}
	},
	setup(props: Props) {
		const { userImage } = toRefs(props);

		return { userImage };
	}
});

interface Props {
	userImage: string;
}
</script>