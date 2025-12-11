/**
 * ProgressBar - 작업 진행률 표시 바
 *
 * 담당자가 입력한 엑셀 작업 현황 진행률을 표시.
 * - 기본: 파란색 바
 * - 완료: 녹색 바
 *
 * Block: components.progress-bar
 */

interface ProgressBarProps {
  // 진행률 (0-100)
  metadataProgress?: number;
  metadataLabel?: string;

  // archive db 진행률 (마커) - deprecated
  archiveProgress?: number;

  // 완료 여부
  isComplete?: boolean;

  // 크기
  size?: 'sm' | 'md' | 'lg';

  // 표시 모드
  showLabel?: boolean;
  showPercentage?: boolean;
}

const SIZE_CLASSES = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
};

export default function ProgressBar({
  metadataProgress = 0,
  metadataLabel,
  archiveProgress,
  isComplete = false,
  size = 'md',
  showLabel = false,
  showPercentage = true,
}: ProgressBarProps) {
  const progress = Math.min(Math.max(metadataProgress, 0), 100);

  return (
    <div className="w-full">
      {/* Label Row */}
      {showLabel && (
        <div className="flex justify-between text-xs mb-0.5">
          <span className="text-blue-600 font-medium">
            {metadataLabel || '작업 진행률'}
          </span>
          {showPercentage && (
            <span className={`font-medium ${isComplete ? 'text-green-600' : 'text-gray-600'}`}>
              {progress.toFixed(0)}%{isComplete && ' ✓'}
            </span>
          )}
        </div>
      )}

      {/* Progress Bar Container */}
      <div className={`relative w-full bg-gray-200 rounded-full ${SIZE_CLASSES[size]} overflow-visible`}>
        {/* Progress (채워진 바) */}
        <div
          className={`absolute top-0 left-0 ${SIZE_CLASSES[size]} rounded-full transition-all duration-300 ${
            isComplete ? 'bg-green-500' : 'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />

        {/* Archive Marker (세로선) */}
        {archiveProgress !== undefined && archiveProgress > 0 && (
          <div
            className="absolute top-0 w-0.5 bg-blue-600 z-10"
            style={{
              left: `${Math.min(archiveProgress, 100)}%`,
              height: '150%',
              top: '-25%',
            }}
            title={`archive: ${archiveProgress.toFixed(0)}%`}
          />
        )}
      </div>

      {/* Inline Percentage (when showLabel is false) */}
      {!showLabel && showPercentage && (
        <div className="text-right mt-0.5">
          <span className={`text-xs ${isComplete ? 'text-green-600' : 'text-gray-500'}`}>
            {progress.toFixed(0)}%{isComplete && ' ✓'}
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * DualProgressBar - 두 개의 진행률 바를 상하로 표시
 */
interface DualProgressBarProps {
  metadataProgress?: number;
  metadataTimecode?: string;
  archiveProgress?: number;
  isComplete?: boolean;
}

export function DualProgressBar({
  metadataProgress = 0,
  metadataTimecode,
  archiveProgress,
  isComplete = false,
}: DualProgressBarProps) {
  return (
    <div className="space-y-1">
      {/* Metadata Bar */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-purple-600 w-16 flex-shrink-0">[metadata]</span>
        <div className="flex-1 relative">
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-300 ${
                isComplete ? 'bg-green-500' : 'bg-purple-500'
              }`}
              style={{ width: `${Math.min(metadataProgress, 100)}%` }}
            />
          </div>
        </div>
        <span className="text-xs text-gray-500 w-20 text-right">
          {metadataProgress.toFixed(0)}% {metadataTimecode && `(${metadataTimecode})`}
        </span>
      </div>

      {/* Archive Marker Line (if exists) */}
      {archiveProgress !== undefined && archiveProgress > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-blue-600 w-16 flex-shrink-0">[archive]</span>
          <div className="flex-1 relative">
            <div className="w-full h-1.5 border-t border-dashed border-gray-300 relative">
              {/* Marker */}
              <div
                className="absolute top-1/2 -translate-y-1/2 w-0.5 h-3 bg-blue-600"
                style={{ left: `${Math.min(archiveProgress, 100)}%` }}
              />
            </div>
          </div>
          <span className="text-xs text-gray-500 w-20 text-right">
            @ {archiveProgress.toFixed(0)}%
          </span>
        </div>
      )}
    </div>
  );
}
