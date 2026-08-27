const env = import.meta.env as Record<string, string | undefined>;

export const CHAT_SOCKET_URL = env.VITE_CHAT_SOCKET_URL || 'ws://localhost:7862/chat';
export const SRS_BASE_URL = env.VITE_SRS_BASE_URL || 'webrtc://localhost/live/livestream';
