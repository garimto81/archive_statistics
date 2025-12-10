import { useQuery } from '@tanstack/react-query';
import { statsApi } from '../services/api';
import type { CodecStats as CodecStatsType } from '../types';

interface CodecStatsProps {
  extensions?: string[];
}

function CodecBar({ codec, maxCount }: { codec: CodecStatsType; maxCount: number }) {
  const widthPercent = (codec.file_count / maxCount) * 100;
  const isVideo = codec.codec_type === 'video';
  const bgColor = isVideo ? 'bg-blue-500' : 'bg-green-500';
  const bgColorLight = isVideo ? 'bg-blue-100' : 'bg-green-100';

  return (
    <div className="flex items-center gap-3 py-1.5">
      <div className="w-16 text-sm font-mono text-gray-700 truncate" title={codec.codec_name}>
        {codec.codec_name}
      </div>
      <div className={`flex-1 h-5 ${bgColorLight} rounded-full overflow-hidden`}>
        <div
          className={`h-full ${bgColor} rounded-full transition-all duration-300`}
          style={{ width: `${widthPercent}%` }}
        />
      </div>
      <div className="w-20 text-right text-sm text-gray-600">
        {codec.file_count.toLocaleString()}
      </div>
      <div className="w-20 text-right text-xs text-gray-500">
        {codec.total_size_formatted}
      </div>
    </div>
  );
}

export default function CodecStats({ extensions }: CodecStatsProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['codecs', extensions],
    queryFn: () => statsApi.getCodecs(10, extensions),
    staleTime: 30000,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <div className="animate-pulse">
          <div className="h-5 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-5 bg-gray-100 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <p className="text-red-500 text-sm">코덱 정보를 불러올 수 없습니다</p>
      </div>
    );
  }

  const videoMaxCount = Math.max(...data.video_codecs.map((c) => c.file_count), 1);
  const audioMaxCount = Math.max(...data.audio_codecs.map((c) => c.file_count), 1);

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">코덱 분포</h3>

      {/* Video Codecs */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-blue-600">비디오 코덱</h4>
          <span className="text-xs text-gray-500">
            {data.total_video_files.toLocaleString()}개 파일
          </span>
        </div>
        {data.video_codecs.length > 0 ? (
          <div className="space-y-1">
            {data.video_codecs.map((codec) => (
              <CodecBar key={codec.codec_name} codec={codec} maxCount={videoMaxCount} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">코덱 정보 없음</p>
        )}
      </div>

      {/* Audio Codecs */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-green-600">오디오 코덱</h4>
          <span className="text-xs text-gray-500">
            {data.total_audio_analyzed.toLocaleString()}개 분석됨
          </span>
        </div>
        {data.audio_codecs.length > 0 ? (
          <div className="space-y-1">
            {data.audio_codecs.map((codec) => (
              <CodecBar key={codec.codec_name} codec={codec} maxCount={audioMaxCount} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">코덱 정보 없음</p>
        )}
      </div>
    </div>
  );
}
