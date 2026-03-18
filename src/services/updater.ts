export type UpdaterStage =
  | 'unsupported'
  | 'checking'
  | 'up-to-date'
  | 'available'
  | 'downloading'
  | 'installed'
  | 'error';

export interface UpdaterProgress {
  downloadedBytes: number;
  totalBytes: number;
  percent: number | null;
}

export interface UpdaterState {
  stage: UpdaterStage;
  version?: string;
  notes?: string;
  progress?: UpdaterProgress;
  error?: string;
}

type DownloadEventLike =
  | { event: 'Started'; data: { contentLength: number } }
  | { event: 'Progress'; data: { chunkLength: number } }
  | { event: 'Finished'; data: Record<string, unknown> };

type UpdateHandleLike = {
  version: string;
  body?: string;
  downloadAndInstall: (onEvent?: (event: DownloadEventLike) => void) => Promise<void>;
};

export function isTauriDesktopRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

export async function checkDesktopUpdate(): Promise<{ state: UpdaterState; update: UpdateHandleLike | null }> {
  if (!isTauriDesktopRuntime()) {
    return {
      state: {
        stage: 'unsupported',
      },
      update: null,
    };
  }

  try {
    const updater = await import('@tauri-apps/plugin-updater');
    const update = (await updater.check()) as UpdateHandleLike | null;

    if (!update) {
      return {
        state: {
          stage: 'up-to-date',
        },
        update: null,
      };
    }

    return {
      state: {
        stage: 'available',
        version: update.version,
        notes: update.body,
      },
      update,
    };
  } catch (error: unknown) {
    return {
      state: {
        stage: 'error',
        error: error instanceof Error ? error.message : 'Updater check failed',
      },
      update: null,
    };
  }
}

export async function downloadAndInstallDesktopUpdate(
  update: UpdateHandleLike,
  onProgress?: (progress: UpdaterProgress) => void,
): Promise<UpdaterState> {
  let downloadedBytes = 0;
  let totalBytes = 0;

  try {
    await update.downloadAndInstall((event) => {
      if (event.event === 'Started') {
        totalBytes = Number(event.data.contentLength || 0);
        downloadedBytes = 0;
      }

      if (event.event === 'Progress') {
        downloadedBytes += Number(event.data.chunkLength || 0);
      }

      if (event.event === 'Started' || event.event === 'Progress') {
        onProgress?.({
          downloadedBytes,
          totalBytes,
          percent: totalBytes > 0 ? Math.min(100, Math.round((downloadedBytes / totalBytes) * 100)) : null,
        });
      }
    });

    return {
      stage: 'installed',
      version: update.version,
      notes: update.body,
    };
  } catch (error: unknown) {
    return {
      stage: 'error',
      error: error instanceof Error ? error.message : 'Updater install failed',
      version: update.version,
    };
  }
}
