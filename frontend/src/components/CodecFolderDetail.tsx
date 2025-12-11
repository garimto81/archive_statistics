/**
 * CodecFolderDetail - 폴더 코덱 상세 정보 컴포넌트
 *
 * 선택된 폴더의 코덱 분포 및 파일 목록을 표시.
 * Progress API를 사용하여 FolderTreeWithProgress와 통합.
 *
 * Block: components.codec-detail
 */
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Film, Volume2, FileVideo } from 'lucide-react';
import clsx from 'clsx';
import { progressApi } from '../services/api';
import type { FileWithProgress } from '../types';

// ==================== Helper Functions ====================

/**
 * 코덱명 포맷팅 (대문자로 표시)
 */
function formatCodecName(codec: string | null | undefined): string {
  if (!codec) return '-';
  return codec.toUpperCase();
}

/**
 * 코덱에 따른 색상 클래스 반환
 */
function getCodecColorClass(codec: string | null | undefined, type: 'video' | 'audio'): string {
  if (!codec) return 'text-gray-400';

  const codecLower = codec.toLowerCase();

  if (type === 'video') {
    if (['hevc', 'h265', 'h.265'].includes(codecLower)) return 'text-blue-600';
    if (['h264', 'h.264', 'avc', 'avc1'].includes(codecLower)) return 'text-green-600';
    if (['av1'].includes(codecLower)) return 'text-purple-600';
    return 'text-gray-600';
  } else {
    if (['aac'].includes(codecLower)) return 'text-orange-600';
    if (['ac3', 'eac3', 'ac-3'].includes(codecLower)) return 'text-red-600';
    if (['dts'].includes(codecLower)) return 'text-pink-600';
    return 'text-gray-600';
  }
}

// ==================== Main Component ====================

interface CodecFolderDetailProps {
  folderPath: string;
  onFileSelect?: (file: FileWithProgress) => void;
}

export default function CodecFolderDetail({
  folderPath,
  onFileSelect,
}: CodecFolderDetailProps) {
  // Progress API 사용 (include_files=true)
  const { data: folder, isLoading, error } = useQuery({
    queryKey: ['codec-folder-detail', folderPath],
    queryFn: () => progressApi.getFolderDetail(folderPath, true),
    enabled: !!folderPath,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-5 h-5 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (error || !folder) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="text-center py-8 text-gray-500 text-sm">
          폴더 정보를 불러올 수 없습니다.
        </div>
      </div>
    );
  }

  // codec_summary는 include_codecs=true일 때만 반환됨
  // 상세 보기에서는 파일 목록에서 직접 계산
  const files = folder.files || [];

  // 코덱 통계 계산
  const videoCodecs: Record<string, number> = {};
  const audioCodecs: Record<string, number> = {};
  let filesWithCodec = 0;

  files.forEach((file) => {
    if (file.video_codec) {
      videoCodecs[file.video_codec] = (videoCodecs[file.video_codec] || 0) + 1;
      filesWithCodec++;
    }
    if (file.audio_codec) {
      audioCodecs[file.audio_codec] = (audioCodecs[file.audio_codec] || 0) + 1;
    }
  });

  const topVideoCodec = Object.entries(videoCodecs).sort(([, a], [, b]) => b - a)[0]?.[0] || null;
  const topAudioCodec = Object.entries(audioCodecs).sort(([, a], [, b]) => b - a)[0]?.[0] || null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      {/* Header */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-900 truncate">{folder.name}</h4>
        <p className="text-xs text-gray-500 truncate">{folder.path}</p>
      </div>

      {/* Codec Summary Stats */}
      {(Object.keys(videoCodecs).length > 0 || Object.keys(audioCodecs).length > 0) && (
        <div className="mb-4">
          <h5 className="text-xs font-medium text-gray-700 mb-2">코덱 분포</h5>

          {/* Video Codecs */}
          {Object.keys(videoCodecs).length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-1 mb-1">
                <Film className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs text-gray-500">Video Codecs</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(videoCodecs)
                  .sort(([, a], [, b]) => b - a)
                  .map(([codec, count]) => (
                    <span
                      key={codec}
                      className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        codec === topVideoCodec
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-600'
                      )}
                    >
                      {formatCodecName(codec)} ({count})
                    </span>
                  ))}
              </div>
            </div>
          )}

          {/* Audio Codecs */}
          {Object.keys(audioCodecs).length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-1 mb-1">
                <Volume2 className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs text-gray-500">Audio Codecs</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(audioCodecs)
                  .sort(([, a], [, b]) => b - a)
                  .map(([codec, count]) => (
                    <span
                      key={codec}
                      className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        codec === topAudioCodec
                          ? 'bg-orange-100 text-orange-700'
                          : 'bg-gray-100 text-gray-600'
                      )}
                    >
                      {formatCodecName(codec)} ({count})
                    </span>
                  ))}
              </div>
            </div>
          )}

          {/* Coverage Stats */}
          <div className="bg-gray-50 rounded p-2 text-xs">
            <div className="flex justify-between mb-1">
              <span className="text-gray-500">코덱 분석 완료</span>
              <span className="font-medium">
                {filesWithCodec} / {files.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-green-500 transition-all"
                style={{
                  width: files.length > 0
                    ? `${(filesWithCodec / files.length) * 100}%`
                    : '0%'
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* General Stats */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">파일 수</span>
          <span className="float-right font-medium">{folder.file_count}</span>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">용량</span>
          <span className="float-right font-medium">{folder.size_formatted}</span>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">재생시간</span>
          <span className="float-right font-medium">{folder.duration_formatted}</span>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">하위 폴더</span>
          <span className="float-right font-medium">{folder.folder_count}</span>
        </div>
      </div>

      {/* Files List */}
      {files.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-gray-500 mb-2">
            파일 목록 ({files.length})
          </h5>
          <div className="max-h-[300px] overflow-y-auto space-y-1">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer text-xs border border-gray-100"
                onClick={() => onFileSelect?.(file)}
              >
                <FileVideo className="w-4 h-4 text-purple-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="truncate font-medium" title={file.name}>
                    {file.name}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 text-gray-400">
                    <span>{file.size_formatted}</span>
                    <span>·</span>
                    <span>{file.duration_formatted}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
                  <span className={clsx('font-medium', getCodecColorClass(file.video_codec, 'video'))}>
                    {formatCodecName(file.video_codec)}
                  </span>
                  <span className={clsx('font-medium', getCodecColorClass(file.audio_codec, 'audio'))}>
                    {formatCodecName(file.audio_codec)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No files message */}
      {files.length === 0 && (
        <div className="text-center py-4 text-gray-400 text-xs">
          이 폴더에 파일이 없습니다.
        </div>
      )}
    </div>
  );
}
