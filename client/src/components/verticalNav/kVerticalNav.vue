<template>
<nav id="verticalNav" class="navbar navbar-vertical">
	<div id="verticalNavHead" class="d-flex align-items-center ms-2">
		<div class="toggle-icon-wrapper me-2">
			<button class="btn navbar-vertical-toggle" v-kd-tooltip="{title: 'Toggle Navigation', placement: 'left'}">
				<font-awesome-icon :icon="['fa', 'bars']" />
				<span class="visually-hidden">Toggle Dropdown</span>
			</button>
		</div>
		<a class="navbar-brand" :href="brand.route">
			<div class="d-flex align-items-center py-3">
				<img class="me-2" :src="brand.image.source" :alt="`${brand.image.alt} logo`" :width="brand.image.width">
				<span class="font-sans-serif" id="title">{{ brand.image.title }}</span>
			</div>
		</a>
	</div>
	<div id="navbarVerticalCollapse" class="collapse navbar-collapse" ref="collapseEl">
		<kCard>
			<div class="navbar-vertical-content scrollbar perfect-scrollbar">
				<div class="navbar-nav flex-column mb-3">
					<!-- nav links here -->
					<slot />
				</div>
			</div>
		</kCard>
	</div>
</nav>
</template>

<script lang="ts">
import { toRefs, onMounted, defineComponent, PropType, ref, watch } from "vue";
import { Brand } from "../kPageNavigation.vue";
import kdTooltip from "../../directives/kdTooltip";
import kCard from "../cards/kCard.vue";
import {getItemFromStore} from "../../helpers/helpers";
import Collapse from "bootstrap/js/dist/collapse.js";

export default defineComponent({
	props: {
		brand: {type: Object as PropType<Brand>, default: "", validator(b: Brand): b is Brand {return typeof b.route !== "undefined"}}
	},
	components: {kCard},
	directives: {[kdTooltip.dName]: kdTooltip.dInit},
	setup(props: Props) {
		const { brand } = toRefs(props);
		let collapseEl = ref();

		onMounted(() => {
			// Open or close the menu based on what the user set last
			const collapse = getItemFromStore("isNavbarVerticalCollapsed", "false");

			if (collapse === true)
				(document.querySelector("html") || new Element).classList.add("navbar-vertical-collapsed");

			if (collapseEl.value)
				new Collapse(collapseEl.value, {toggle: false});
		});

		return { brand, collapseEl };
	}
});

interface Props {
	brand: Brand;
}
</script>

<style lang="scss">
@media (max-width: 1200px) {
	#verticalNav .navbar-brand {
		display: none;
	}
}
#verticalNav {
	max-width: 13rem;
	align-items: unset !important;
	z-index: 1000;
}
#verticalNav #title {
	color: var(--primaryColor) !important;
}
#verticalNav .navbar-collapse {
	display: inline-block !important;
	max-width: 13rem;
}
#verticalNavHead {
	height: 3.5rem;
}
#navbarVerticalCollapse {
	flex-basis: unset;
	width: 100%;
}
#navbarVerticalCollapse .card {
	background-image: linear-gradient(45deg, var(--primaryColor), var(--primaryDark));
	background-color: #FFFFFF00 !important;
	height: 100%;
	width: 13rem;
}
#navbarVerticalCollapse .card-body {
	background-color: #FFFFFF00 !important;
	padding-top: 0px;
	padding-left: 0.355rem;
}
.navbar-vertical {
	position: fixed !important;
    display: inline-block;
	flex-direction: column;
	height: 100vh;
}
.nav-link {
	color: #FFFFFFBF !important;
}
.nav-link:hover, .nav-link:focus {
	color: white;
}
#verticalNav .nav-link {
	border-left: 2px solid #FFFFFF00;
	padding-left: 0.6rem;
}
#verticalNav .nav-link-icon {
	padding-right: 1rem;
}
#verticalNav .router-link-active {
	border-left: 2px solid white;
	color: white !important;
}
.navbar-vertical-collapsed #navbarVerticalCollapse {
	width: 3.4rem !important;
	overflow: hidden;
	border-radius: .25rem;
}
</style>