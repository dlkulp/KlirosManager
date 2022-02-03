<template>
<kFluidLayout>
	<kVerticalNav :brand="brand">
		<slot name="mainNav" />
	</kVerticalNav>
	<div class="content">
		<kTopNav :brand="brand">
			<template #right>
				<slot name="topRight" />
			</template>
			<template #left>
				<slot name="topLeft" />
			</template>
		</kTopNav>
		<slot name="pageContent" />
	</div>
</kFluidLayout>
</template>

<script lang="ts">
import kFluidLayout from "./kFluidLayout.vue";
import kVerticalNav from "./verticalNav/kVerticalNav.vue";
import kTopNav from "./kTopNav.vue";
import { onMounted, toRefs, Ref, defineComponent } from "vue";
import {getItemFromStore, setItemToStore, hasClass} from "../helpers/helpers";

interface BrandImage {
	source: string;
	width: number;
	title: string;
	alt: string;
}

export interface Brand {
	image: BrandImage;
	route: string;
}

export default defineComponent({
	components: {kFluidLayout, kVerticalNav, kTopNav},
	props: {
		brand: {type: Object, default: "", validator(b: Brand): b is Brand {return typeof b.route !== "undefined"}}
	},
	setup(props: Props) {
		const { brand } = toRefs(props);
		onMounted(handleNavbarVerticalCollapsed);
		
		return {brand: brand as Ref<Brand>};
	}
});

const handleNavbarVerticalCollapsed = () => {
	const navbarVerticalToggle = document.querySelector(".navbar-vertical-toggle") as HTMLElement;
	const html = document.querySelector("html") as HTMLElement;
	const navbarVerticalCollapse = document.querySelector(".navbar-vertical .navbar-collapse") as HTMLElement;

	if (navbarVerticalToggle) {
		navbarVerticalToggle.addEventListener("click", (e) => {
			navbarVerticalToggle.blur();
			html.classList.toggle("navbar-vertical-collapsed");

			// Set collapse state on localStorage
			const isNavbarVerticalCollapsed = getItemFromStore("isNavbarVerticalCollapsed");
			setItemToStore("isNavbarVerticalCollapsed",(!isNavbarVerticalCollapsed).toString());

			const event = new CustomEvent("navbar.vertical.toggle");
			e.currentTarget?.dispatchEvent(event);
		});
	}
	if (navbarVerticalCollapse) {
		navbarVerticalCollapse.addEventListener("mouseover", () => {
			if (hasClass(html, "navbar-vertical-collapsed"))
				html.classList.add("navbar-vertical-collapsed-hover");
		});
		navbarVerticalCollapse.addEventListener("mouseleave", () => {
			if (hasClass(html, "navbar-vertical-collapsed-hover"))
				html.classList.remove("navbar-vertical-collapsed-hover");
		});
	}
};

interface Props {
	brand: Object;
}
</script>

<style lang="scss">
.content {
	height:100vh;
	margin-left: 14rem;
}

.navbar-vertical-collapsed .content {
	margin-left: 4.1rem !important;
}
</style>