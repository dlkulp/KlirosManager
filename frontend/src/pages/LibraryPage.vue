<template>
  <q-page>
    <div id="card-container" class="flex justify-center items-center column">
      <h4>Library</h4>
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <ScoreGrid v-if="allWorks" justify="center" :score-arr="allWorks"></ScoreGrid>
      <q-pagination
        v-if="pageCount > 1"
        v-model="page"
        :max="pageCount"
        :max-pages="7"
        @update:model-value="loadWorks"
      />
    </div>
  </q-page>
</template>

<style lang="scss" scoped>
h1 {font-size: 3rem}
h2 {font-size: 2rem}
h4 {margin: 2rem 0rem 1rem}
</style>

<script setup lang="ts">
import ScoreGrid, {
  type ScoreGridProps
} from "@/components/ScoreGrid.vue";
import { onMounted, ref } from "vue";
import { ResourceDto, KlirosApi, InferredMetadataValueDto } from "@/types/api-client";
//import { getAttribution } from "@/helpers/helpers";

const allWorks = ref<ResourceDto[]>();
const emptyMessage = ref("");
const page = ref(1);
const pageCount = ref(0);
const api = new KlirosApi();
let requestSequence = 0;

function getAttribution(metaData: any) {
  if (metaData?.Composer?.value)
    return `By ${metaData.Composer.value}`;
  else if (metaData?.Arranger?.value)
    return `Arr. ${metaData.Arranger.value}`;
  else
    return "Unknown Composer";
}

async function loadWorks() {
  const sequence = ++requestSequence;
  emptyMessage.value = "";
  try {
    const result = await api.search({ page: page.value, page_size: 24 });
    if (sequence !== requestSequence) return;
    allWorks.value = result.results;
    page.value = result.page;
    pageCount.value = result.page_count;
    if (allWorks.value.length === 0) {
      emptyMessage.value = "Nothing to see here!";
    }
  } catch {
    if (sequence !== requestSequence) return;
    allWorks.value = undefined;
    emptyMessage.value = "Library could not be loaded.";
  }
}

onMounted(loadWorks);
</script>
