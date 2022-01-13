<script setup lang="ts">
import Card from "primevue/card";
import Chip from "primevue/chip";

interface GridItems {
	img: {
		url: string,
		alt: string
	};
	title: string;
	tags?: string[];
	metaData: object;
	id: string;
}

defineProps<{ grid: GridItems[] }>();
</script>

<template>
	<div class="grid">
		<Card v-for="card in grid">
			<template #header>
				<div class="trim">
					<img :alt="card.img.alt" :src="card.img.url">
				</div>
			</template>
			<template #title>
				{{card.title}}
			</template>
			<template #content>
				<Chip v-for="tag in card.tags" :label="tag" class="p-mr-2 p-mb-2" />
			</template>
			<!-- <template #footer>
				<Button icon="pi pi-check" label="Save" />
				<Button icon="pi pi-times" label="Cancel" class="p-button-secondary" style="margin-left: .5em" />
			</template> -->
		</Card>
	</div>
</template>

<style scoped>
.grid {
	padding: 3rem;
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(250px, auto));
	grid-gap: 1rem;
}
.grid .p-card {
	border-radius: .75rem;
}
.trim {
	width: 100%;
    height: 200px;
    overflow: hidden;
}
.p-card img {
	border-top-left-radius: .75rem;
	border-top-right-radius: .75rem;
}
.p-card .p-chip {
	font-size: .75rem;
}
</style>