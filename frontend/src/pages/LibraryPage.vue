<template>
  <q-page>
    <div id="card-container" class="flex justify-center items-center column">
      <h4>Library</h4>
      <p v-if="emptyMessage">{{ emptyMessage }}</p>
      <div id="all-works" class="fit row wrap justify-center items-start content-start">
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
              <p text-caption class="light">{{ getAttribution(score.MetaData) }}</p>
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
.title-section strong {
  font-size: 1.25rem;
}
#all-works a {
  width: 300px;
}
#all-works .q-btn {
  text-transform: none;
}

</style>

<script setup lang="ts">
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
