<template>
<nav id="topNav" class="navbar navbar-light navbar-glass navbar-top navbar-expand">
	<button class="btn navbar-toggler me-1 me-sm-3 collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#navbarVerticalCollapse" aria-controls="navbarVerticalCollapse" aria-expanded="false" aria-label="Toggle Navigation">
		<font-awesome-icon :icon="['fa', 'bars']" />
		<span class="visually-hidden">Toggle Dropdown</span>
	</button>
	<a class="navbar-brand me-1 me-sm-3" :href="brand.route">
		<div class="d-flex align-items-center">
			<img class="me-2" :src="brand.image.source" :alt="`${brand.image.title} logo`" :width="brand.image.width">
			<span class="font-sans-serif">{{ brand.image.title }}</span>
		</div>
	</a>
	<div class="ms-3 ms-sm-0">
		<slot name="left" />
	</div>
	<div class="ms-auto">
		<slot name="right" />
	</div>
</nav>
</template>

<script lang="ts">
import { toRefs, defineComponent, PropType } from "vue";
import { Brand } from "./kPageNavigation.vue";

export default defineComponent({
	props: {
		brand: {type: Object as PropType<Brand>, default: "", validator(b: Brand): b is Brand {return typeof b.route !== "undefined"}}
	},
	setup(props: Props) {
		const {brand} = toRefs(props);

		return { brand };
	}
});

interface Props {
	brand: Brand;
}
</script>

<style lang="scss">
@media (min-width: 1200px) {
	.navbar-vertical+.content .navbar-top .navbar-toggler, 
	.navbar-vertical+.content .navbar-top .navbar-brand {
		display: none;
	}
}

#topNav {
	min-height: 3.5rem;
	position: -webkit-sticky;
    position: sticky;
    top: 0;
    z-index: 900;
    background-color: var(--bs-body-bg);
}
</style>