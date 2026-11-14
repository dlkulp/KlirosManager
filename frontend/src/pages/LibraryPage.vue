<template>
  <q-page>
    <div id="card-container" class="flex justify-center items-center column">
      <h4>Library</h4>
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <div id="recent-works" class="fit row wrap justify-center items-start content-start">
        <q-btn flat
          v-for="(score, index) in allWorks"
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

const allWorks = ref<ResourceDto[]>();
const emptyMessage = ref("");
const api = new KlirosApi();

function getMDAttribution(metaData: any) {
  return metaData?.value || "By Unknown";
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
