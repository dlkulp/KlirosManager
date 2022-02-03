<script setup lang="ts">
import kCard from "../components/cards/kCard.vue";
//import kCardHeader from "../components/cards/kCardHeader.vue";
import kCardText from "../components/cards/kCardText.vue";
import kButton from "../components/kButton.vue";
import kBadge from "../components/kBadge.vue";

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
		<kCard v-for="card in grid" :title="card.title" :imageURL="card.img.url">
			<kCardText class="card-content">
				<kBadge v-for="tag in card.tags" type="pill" class="p-mr-2 p-mb-2">{{tag}}</kBadge>
			<!-- <template #footer>
				<Button icon="pi pi-check" label="Save" />
				<Button icon="pi pi-times" label="Cancel" class="p-button-secondary" style="margin-left: .5em" />
			</template> -->
			</kCardText>
		</kCard>
	</div>
</template>

<style>
.grid {
	padding: 3rem;
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(250px, auto));
	grid-gap: 1rem;
}
.card-img-top {
	width: 100%;
    height: 200px;
    overflow: hidden;
}
</style>