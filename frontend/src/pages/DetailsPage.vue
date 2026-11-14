<template>
  <q-page v-if="detail" class="flex justify-center">
    <div id="score">
      <h4>{{ detail.resource.title || detail.resource.OriginalName || "Untitled" }}</h4>
      <p>{{ detail.resource.OriginalName }}</p>
      <PdfViewer
          v-if="detail"
          :source="detail.file_url"
          style="height: 80vh; width: 80%;"
          :show-thumbnails="false"
          :enable-search="false"
          :enable-download="false"
          :lazy="true"
          :virtualization="true"
        />
      <q-btn color="secondary" to="/" label="Go to Index Page" no-caps />
    </div>
    <!-- <q-card>
      <template v-for="(value, key) in detail.resource.MetaData" :key="key">
        <q-card-section>
          <p>{{ key }}</p>
          <p>{{ value }}</p>
        </q-card-section>
        <q-separator />
      </template>
    </q-card> -->
  </q-page>
</template>

<style scoped lang="scss">
h4 {
  margin-bottom: 0px;
}
#score {
  width:80%
}
</style>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ResourceDetailResponseDto, KlirosApi } from "@/types/api-client";

import { PdfViewer } from "vue-pdfz";
import "vue-pdfz/style.css";

const { scoreId } = defineProps<{
  scoreId: string;
}>();

const detail = ref<ResourceDetailResponseDto | null>(null);
const api = new KlirosApi();

onMounted(async() => {
  try {
    detail.value = await api.getResource(Number(scoreId));
  } catch (error) {
    // detailStatus.textContent = error instanceof Error ? error.message : "The score could not be loaded.";
    // detailStatus.hidden = false;
    console.error(error);
  }

});
</script>
