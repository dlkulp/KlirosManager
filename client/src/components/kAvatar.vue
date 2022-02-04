<template>
	<div id="avatar">
		<img :class="avatarClass" :src="image.src" :alt="image.alt" />
	</div>
</template>

<script lang="ts">
import { toRefs, ref, watch, defineComponent, PropType } from "vue";

function setAvatarClass(shape: string) {
	return `${shape === "rounded" ? shape : ''}`;
}

interface AvatarImage {
	src: string;
	alt: string;
}

export default defineComponent({
	props: {
		shape: {type: String, default: "rounded", validator(s: string) {return ["square", "rounded"].indexOf(s) !== -1}},
		image: {type: Object as PropType<AvatarImage>, default: "", validator(i: AvatarImage): i is AvatarImage {return typeof i.src !== "undefined"}}
	},
	setup(props: Props) {
		const {shape, image} = toRefs(props);
		const avatarClass = ref(setAvatarClass(shape.value));

		watch([shape], ([newShape]) => {
			avatarClass.value = setAvatarClass(newShape as string);
		});

		return {avatarClass, image};
	}
});

interface Props {
	shape: string;
	image: AvatarImage;
}
</script>

<style>
#avatar img {
	width: 2rem;
	background-color: var(--primaryColor);
}
</style>