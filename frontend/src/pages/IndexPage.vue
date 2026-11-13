<template>
  <q-page>
    <header class="flex justify-center items-center column">
      <h1>Recent Additions</h1>
      <q-btn flat to="/library">Browse full library →</q-btn>
    </header>

    <div id="card-container" class="flex">
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <div id="recent-works" class="fit row wrap justify-center items-start content-start">
        <q-card
          v-for="(score, index) in recentWorks"
          :key="`${score.title}-${index}`"
          class="work-card"
        >
          <q-card-section>
            <img
              :src="score.thumbnail_url"
              :srcset="score.thumbnail_srcset || ''"
              sizes="(max-width: 600px) 45vw, (max-width: 900px) 30vw, 300px"
              alt="Score thumbnail"
              loading="lazy"
              width="232"
              height="300" />
          </q-card-section>
          <q-card-section>
            <strong>{{ score.title || score.OriginalName || "Untitled" }}</strong>
            <p>{{ score.MetaData.Composer?.value || score.MetaData.Arranger?.value || "By Unknown" }}</p>
          </q-card-section>
        </q-card>
      </div>
      <!-- <q-btn
        class="q-mt-md"
        color="primary"
        to="/second"
        label="Go to Second Page"
        no-caps
      /> -->
    </div>
  </q-page>
</template>

<style scoped>
h1 {font-size: 3rem}
h2 {font-size: 2rem}
.work-card {
  margin: 10px;
}
</style>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Score } from "@/types/score";

const recentWorks = ref<Score[]>([]);
const emptyMessage = ref("");

onMounted(async () => {
  try {
    const response = await fetch("/api/home");
    if (!response.ok) throw new Error("Could not load recent works.");

    const data = (await response.json()) as { recent_works?: Score[] };
    recentWorks.value = Array.isArray(data.recent_works) ? data.recent_works : [];
    if (recentWorks.value.length === 0) {
      emptyMessage.value = "Nothing to see here!";
    }
  } catch {
    emptyMessage.value = "Recent works could not be loaded.";
  }
});
</script>
