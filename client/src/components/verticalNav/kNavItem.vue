<template>
<div v-if="!$slots.dropdown" class="nav-item">
	<router-link :to="route" class="nav-link">
	<div class="d-flex align-items-center">
		<span class="nav-link-icon"><slot name="icon" /></span>
		<span class="nav-link-text">{{ name }} </span>
		<span v-if="newTag" class="badge rounded-pill badge-soft-success ms-2">
			New
		</span>
	</div>
	</router-link>
</div>
<div v-else class="nav-item">
	<a class="nav-link dropdown-indicator" data-bs-toggle="collapse" :href="`#${cleanName}`" role="button" aria-expanded="false" :aria-controls="cleanName">
		<div class="d-flex align-items-center">
			<span class="nav-link-icon"><slot name="icon" /></span>
			<span class="nav-link-text">{{ name }} </span>
			<span v-if="newTag" class="badge rounded-pill badge-soft-success ms-2">
				New
			</span>
		</div>
	</a>
	<nav :id="cleanName" class="nav collapse" :data-parent="`#${parent}`">
		<slot name="dropdown" />
	</nav>
</div>
</template>

<script lang="ts">
import { toRefs, defineComponent, ref } from "vue";

export default defineComponent({
	props: {
		name: {type: String, default: ""},
		route: {type: String, default: "#", validator(r: string) {return r.startsWith("/") || r.startsWith("#")}},
		parent: {type: String, default: "navbarVerticalCollapse"},
		newTag: {type: Boolean, default: false}
	},
	setup(props: Props) {
		const { name, route, parent, newTag} = toRefs(props);
		const cleanName = ref(name.value.replace(/\s/g, ""));

		return { name, cleanName, route, parent, newTag };
	}
});

interface Props {
	name: string;
	route: string;
	parent: string;
	newTag: boolean;
}
</script>