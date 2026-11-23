<template>
  <q-page>
    <div id="card-container" class="flex justify-center items-center column">
      <h4>Library</h4>
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <ScoreGrid v-if="allWorks" justify="center" :score-arr="allWorks"></ScoreGrid>
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
const api = new KlirosApi();

function getAttribution(metaData: any) {
  if (metaData?.Composer?.value)
    return `By ${metaData.Composer.value}`;
  else if (metaData?.Arranger?.value)
    return `Arr. ${metaData.Arranger.value}`;
  else
    return "Unknown Composer";
}

onMounted(async () => {
  try {
    allWorks.value = (await api.getLibrary()).works;
    if (allWorks.value.length === 0) {
      emptyMessage.value = "Nothing to see here!";
    }
  } catch {
    emptyMessage.value = "Library could not be loaded.";
  }
});
</script>
