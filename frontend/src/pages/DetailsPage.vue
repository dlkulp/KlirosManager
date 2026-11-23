<template>
  <q-page v-if="detail">
    <div id="center-stripe">
      <section class="lighten q-pa-md">
        <h4>{{ title }}</h4>
        <p v-if="!english">{{ detail.resource.DisplayName }}</p>
      </section>
      <section class="row no-wrap justify-between q-mb-xs">
        <q-btn to="/library" icon="arrow_back">Back to Library</q-btn>
        <div right>
          <q-btn outline icon="star" class="q-mr-sm"></q-btn>
          <q-btn color="secondary" :href="detail.download_url" :download="`${detail.resource.DisplayName} - ${attribution}.pdf`" icon="download">Download</q-btn>
        </div>
      </section>
      <section class="row">
        <div id="score" class="col-xs-12 col-md-9 col-xl-10">
          <PdfViewer
              v-if="detail"
              :source="detail.file_url"
              style="width: 98%; margin:auto;"
              :show-thumbnails="false"
              :enable-search="false"
              :enable-download="false"
              :lazy="true"
              :virtualization="true"
              :text-layer="false"
              theme="auto"
            />
        </div>
        <div id="info" class="col-xs-12 col-md-3 col-xl-2 q-pa-md text-body2">
          <h6>Uploaded by:</h6>
          <q-btn outline :to="`/profile/${detail.uploader.UserID}`" class="q-mt-sm q-mb-sm q-pl-sm q-pr-sm">
            <div class="row items-center no-wrap">
              <q-avatar left text-color="white" color="primary" rounded size="2rem">
                {{ detail.uploader_initials }}
              </q-avatar>
              <span class="text-center q-pa-sm text-capitalize text-caption">
                {{ detail.uploader.Name }}<br />
                <span class="text-caption text-weight-thin">Joined: {{ detail.uploader.JoinedAt }}</span>
              </span>
            </div>
          </q-btn>
          <div>
            Downloaded: {{ detail.resource.DownloadCount }} times
          </div>
          <div class="q-mt-md">
            <h6>At a glance:</h6>
            <q-card>
              <q-card-section>
                <template  v-for="(value, key) in detail.metadata" :key="key">
                  <p class="q-mb-xs">{{ key }}</p>
                  <p class="text-caption text-weight-thin">{{ value }}</p>
                </template>
              </q-card-section>
            </q-card>
          </div>
          <div class="q-mt-md" id="actions">
            <h6>Actions:</h6>
            <div class="">
              <template v-if="owner">
                <q-btn outline icon="edit" color="info" class="text-body2 q-ma-xs">&nbsp;Edit</q-btn>
                <q-btn icon="delete" color="negative" class="text-body2 q-ma-xs">&nbsp;Delete</q-btn>
              </template>
              <q-btn icon="flag" color="warning" class="text-body2 q-ma-xs">&nbsp;Report</q-btn>
            </div>
          </div>
        </div>
      </section>
    </div>
  </q-page>
</template>

<style scoped lang="scss">
h4 {
  margin-bottom: 0px;
  margin-top: 1.2rem;
}
h6 {
  margin-bottom: 0px;
  margin-top: 0px;
}
@media only screen and (min-width: 1440px) {
  #center-stripe {
    width: 75%;
    margin-left:auto;
    margin-right:auto;
  }
}
#center-stripe {
  max-width: 1200px;
  margin-left:auto;
  margin-right:auto;
}
#info {
  height: auto !important;
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
const title = ref<string>();
const english = ref<boolean>(true);
const attribution = ref<string>();
const owner = ref<boolean>(false);

onMounted(async() => {
  try {
    detail.value = await api.getResource(Number(scoreId));
    english.value = detail.value.metadata?.["English Title"] === undefined;
    title.value = detail.value.metadata?.["English Title"] || detail.value.resource.title || "Untitled";
    attribution.value = detail.value.metadata?.["Composer"] || detail.value.metadata?.["Arranger"] || "Unknown";
    owner.value = detail.value.uploader.UserID === 1;
    let joinDate = new Date(detail.value.uploader.JoinedAt);
    detail.value.uploader.JoinedAt = `${joinDate.getMonth()+1}/${joinDate.getFullYear()}`;
  } catch (error) {
    // detailStatus.textContent = error instanceof Error ? error.message : "The score could not be loaded.";
    // detailStatus.hidden = false;
    console.error(error);
  }

});
</script>
