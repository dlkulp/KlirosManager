<script setup lang="ts">
import {toRefs, ref, watch, defineEmits} from "vue";
import kCard from "../components/cards/kCard.vue";
//import kCardHeader from "../components/cards/kCardHeader.vue";
import kCardText from "../components/cards/kCardText.vue";
import kButton from "../components/kButton.vue";
import kBadge from "../components/kBadge.vue";
import { makeRequestAsync } from "../helpers/helpers";

export interface GridItems {
	img: {
		url: string,
		alt: string
	};
	DisplayName: string;
	Tags?: string[];
	MetaData: object;
	id: string;
}

async function deleteResource(id: string) {
	await makeRequestAsync({ url: `/api/v1/scores/${id}`, verb: "delete"}).catch(err => {
		console.error(err);
	});
	let idx = grid.value.findIndex(x => x.id == id);
	if (idx != -1)
		grid.value.splice(idx, 1);
}

let props = defineProps<{ 
	modelValue: GridItems[],
	deleteItems?: boolean
}>();

const {modelValue} = toRefs(props);
const grid = ref(modelValue.value);

const emit = defineEmits<{
  (e: "update:modelValue", v: any): void;
}>();

watch(grid, newVal => emit("update:modelValue", newVal));
watch(modelValue, newVal => grid.value = newVal);
</script>

<template>
	<div class="grid">
		<kCard v-for="card in grid" :title="card.DisplayName" :imageURL="card.img.url">
			<div v-if="deleteItems" @click="deleteResource(card.id)" class="close"><font-awesome-icon :icon="['fa', 'xmark']" /></div>
			<kCardText class="card-content">
				<kBadge v-for="tag in card.Tags" type="pill" class="p-mr-2 p-mb-2">{{tag}}</kBadge>
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
.grid .close {
	position: absolute;
	top: 0;
	right: 0;
	padding: 0rem .5rem;
    margin: 3px;
    border: 1px solid #FFFFFF00;
	border-radius: 0.5rem;
}

.grid .close:hover {
	border: 1px var(--bs-primary) solid;
}
</style>