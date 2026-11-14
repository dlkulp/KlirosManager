<template>
  <q-page>
    <header class="flex justify-center items-center column">
      <h1>Recent Additions</h1>
      <q-btn flat to="/library">Browse full library →</q-btn>
    </header>

    <div id="card-container" class="flex">
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <div id="recent-works" class="fit row wrap justify-center items-start content-start">
        <q-btn flat
          v-for="(score, index) in recentWorks"
          :key="`${score.title}-${index}`"
          :to="score.detail_url">
          <q-card>
            <q-card-section>
              <img
                :src="score.thumbnail_url || ''"
                :srcset="score.thumbnail_srcset || ''"
                sizes="(max-width: 600px) 45vw, (max-width: 900px) 30vw, 300px"
                alt="Score thumbnail"
                loading="lazy"
                width="232"
                height="300" />
            </q-card-section>
            <q-card-section class="title-section">
              <strong>{{ score.title || score.OriginalName || "Untitled" }}</strong>
              <p text-caption class="light">{{ getMDAttribution(score.MetaData?.Composer || score.MetaData?.Arranger) }}</p>
            </q-card-section>
          </q-card>
        </q-btn>
      </div>
    </div>
  </q-page>
</template>

<style lang="scss" scoped>
h1 {font-size: 3rem}
h2 {font-size: 2rem}
.title-section {
  padding-top: 0px;
}
.title-section p {
  color: $grey-6
}
</style>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ResourceDto, KlirosApi } from "@/types/api-client";

const recentWorks = ref<ResourceDto[]>();
const emptyMessage = ref("");
const api = new KlirosApi();
function getMDAttribution(metaData: any) {
  return metaData?.value || "By Unknown";
}

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
