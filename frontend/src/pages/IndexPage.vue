<template>
  <q-page>
    <header class="flex justify-center items-center column">
      <h1>Recent Additions</h1>
      <q-btn flat to="/library">Browse full library →</q-btn>
    </header>

    <div id="card-container" class="flex">
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <ScoreGrid v-if="recentWorks" justify="center" :score-arr="recentWorks"></ScoreGrid>
    </div>
  </q-page>
</template>

<style lang="scss" scoped>
h1 {font-size: 3rem}
h2 {font-size: 2rem}
</style>

<script setup lang="ts">
import ScoreGrid, {
  type ScoreGridProps
} from "@/components/ScoreGrid.vue";
import { onMounted, ref } from "vue";
import { ResourceDto, KlirosApi } from "@/types/api-client";
import { getAttribution } from "@/helpers/helpers";

const recentWorks = ref<ResourceDto[]>();
const emptyMessage = ref("");
const api = new KlirosApi();

onMounted(async () => {
  try {
    recentWorks.value = (await api.getHome()).recent_works;
    if (recentWorks.value.length === 0) {
      emptyMessage.value = "Nothing to see here!";
    }
  } catch {
    emptyMessage.value = "Recent works could not be loaded.";
  }
});
</script>
