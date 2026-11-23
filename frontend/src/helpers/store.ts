import { ProfileResponseDto, PublicProfileResponseDto } from "@/types/api-client";
import {reactive} from "vue";

export interface state {
  isLoggedIn: boolean,
  user: ProfileResponseDto | null
}

export const store = reactive<state>({
  isLoggedIn: false,
  user: null
})
