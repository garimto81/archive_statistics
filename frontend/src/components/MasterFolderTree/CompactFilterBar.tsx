/**
 * CompactFilterBar - 한 줄 필터바 컴포넌트
 *
 * 제목과 필터 옵션을 한 줄에 배치하여 공간 절약
 * - 확장자 필터 (드롭다운)
 * - 숨김 파일 토글
 * - 표시 옵션 토글 (진행률, 코덱, 파일)
 *
 * PRD: PRD-0033-FOLDER-TREE-UNIFICATION.md Section 5
 */
import { useState, useRef, useEffect } from 'react';
import {
  Filter,
  Eye,
  EyeOff,
  BarChart3,
  Film,
  FileText,
  ChevronDown,
  Check,
  X,
  RefreshCw,
  Search,
} from 'lucide-react';
import clsx from 'clsx';

// 확장자 그룹 (빠른 선택용)
const EXTENSION_GROUPS = {
  all: { label: 'All', extensions: [] },
  video: { label: 'Video', extensions: ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v'] },
  audio: { label: 'Audio', extensions: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a'] },
  image: { label: 'Image', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'] },
};

interface ExtensionFilterConfig {
  enabled: boolean;
  selected: string[];
  available: string[];
  onChange: (exts: string[]) => void;
}

interface HiddenFilterConfig {
  enabled: boolean;
  show: boolean;
  onChange: (show: boolean) => void;
}

interface DisplayOptionsConfig {
  showProgress?: boolean;
  showCodec?: boolean;
  showFiles?: boolean;
  onChange: (key: 'showProgress' | 'showCodec' | 'showFiles', value: boolean) => void;
}

interface CompactFilterBarProps {
  title: string;
  filters?: {
    extensions?: ExtensionFilterConfig;
    hidden?: HiddenFilterConfig;
    display?: DisplayOptionsConfig;
  };
  actions?: React.ReactNode;
  onRefresh?: () => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  className?: string;
}

export default function CompactFilterBar({
  title,
  filters,
  actions,
  onRefresh,
  searchQuery,
  onSearchChange,
  className,
}: CompactFilterBarProps) {
  const [isExtDropdownOpen, setIsExtDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsExtDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const { extensions, hidden, display } = filters || {};

  // 선택된 확장자 요약 텍스트
  const getExtensionSummary = () => {
    if (!extensions?.selected.length) return 'All';
    if (extensions.selected.length <= 2) return extensions.selected.join(', ');
    return `${extensions.selected.length} selected`;
  };

  // 확장자 그룹 선택
  const handleGroupSelect = (groupKey: keyof typeof EXTENSION_GROUPS) => {
    if (!extensions) return;
    const group = EXTENSION_GROUPS[groupKey];
    if (groupKey === 'all') {
      extensions.onChange([]);
    } else {
      const availableInGroup = group.extensions.filter((ext) =>
        extensions.available.includes(ext)
      );
      extensions.onChange(availableInGroup);
    }
  };

  // 개별 확장자 토글
  const toggleExtension = (ext: string) => {
    if (!extensions) return;
    const newSelected = extensions.selected.includes(ext)
      ? extensions.selected.filter((e) => e !== ext)
      : [...extensions.selected, ext];
    extensions.onChange(newSelected);
  };

  return (
    <div
      data-testid="compact-filter-bar"
      className={clsx(
        'flex items-center justify-between gap-3 px-4 py-2 bg-white border-b border-gray-200',
        className
      )}
    >
      {/* 좌측: 제목 */}
      <h2 className="text-lg font-semibold text-gray-900 whitespace-nowrap">{title}</h2>

      {/* 중앙: 필터 옵션들 */}
      <div className="flex items-center gap-2 flex-1 justify-center">
        {/* 확장자 필터 드롭다운 */}
        {extensions?.enabled && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsExtDropdownOpen(!isExtDropdownOpen)}
              className={clsx(
                'flex items-center gap-1.5 px-2.5 py-1.5 text-sm rounded-lg border transition-colors',
                extensions.selected.length > 0
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
              )}
            >
              <Filter className="w-3.5 h-3.5" />
              <span>{getExtensionSummary()}</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {/* 드롭다운 메뉴 */}
            {isExtDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                {/* 그룹 선택 */}
                <div className="p-2 border-b border-gray-100">
                  <div className="text-xs text-gray-500 mb-1.5">Quick Select</div>
                  <div className="flex gap-1">
                    {Object.entries(EXTENSION_GROUPS).map(([key, group]) => (
                      <button
                        key={key}
                        onClick={() => handleGroupSelect(key as keyof typeof EXTENSION_GROUPS)}
                        className={clsx(
                          'px-2 py-1 text-xs rounded transition-colors',
                          (key === 'all' && extensions.selected.length === 0) ||
                            (key !== 'all' &&
                              group.extensions.every((ext) => extensions.selected.includes(ext)))
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        )}
                      >
                        {group.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 개별 확장자 */}
                <div className="p-2 max-h-48 overflow-y-auto">
                  <div className="grid grid-cols-3 gap-1">
                    {extensions.available.slice(0, 15).map((ext) => (
                      <button
                        key={ext}
                        onClick={() => toggleExtension(ext)}
                        className={clsx(
                          'flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors',
                          extensions.selected.includes(ext)
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                        )}
                      >
                        {extensions.selected.includes(ext) && <Check className="w-3 h-3" />}
                        {ext}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 하단 액션 */}
                <div className="p-2 border-t border-gray-100 flex justify-between">
                  <button
                    onClick={() => extensions.onChange([])}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    Clear
                  </button>
                  <button
                    onClick={() => setIsExtDropdownOpen(false)}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 숨김 파일 토글 */}
        {hidden?.enabled && (
          <button
            data-testid="hidden-files-toggle"
            onClick={() => hidden.onChange(!hidden.show)}
            className={clsx(
              'flex items-center gap-1.5 px-2.5 py-1.5 text-sm rounded-lg border transition-colors',
              hidden.show
                ? 'bg-purple-50 border-purple-200 text-purple-700'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            )}
            title={hidden.show ? 'Hide hidden files' : 'Show hidden files'}
          >
            {hidden.show ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Hidden</span>
          </button>
        )}

        {/* 표시 옵션 토글들 */}
        {display?.showProgress !== undefined && (
          <button
            onClick={() => display.onChange('showProgress', !display.showProgress)}
            className={clsx(
              'flex items-center gap-1.5 px-2.5 py-1.5 text-sm rounded-lg border transition-colors',
              display.showProgress
                ? 'bg-green-50 border-green-200 text-green-700'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            )}
            title={display.showProgress ? 'Hide progress bars' : 'Show progress bars'}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Progress</span>
          </button>
        )}

        {display?.showCodec !== undefined && (
          <button
            onClick={() => display.onChange('showCodec', !display.showCodec)}
            className={clsx(
              'flex items-center gap-1.5 px-2.5 py-1.5 text-sm rounded-lg border transition-colors',
              display.showCodec
                ? 'bg-orange-50 border-orange-200 text-orange-700'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            )}
            title={display.showCodec ? 'Hide codec badges' : 'Show codec badges'}
          >
            <Film className="w-3.5 h-3.5" />
            <span>Codec</span>
          </button>
        )}

        {display?.showFiles !== undefined && (
          <button
            onClick={() => display.onChange('showFiles', !display.showFiles)}
            className={clsx(
              'flex items-center gap-1.5 px-2.5 py-1.5 text-sm rounded-lg border transition-colors',
              display.showFiles
                ? 'bg-cyan-50 border-cyan-200 text-cyan-700'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            )}
            title={display.showFiles ? 'Hide file list' : 'Show file list'}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Files</span>
          </button>
        )}
      </div>

      {/* 우측: 검색 + 액션 */}
      <div className="flex items-center gap-2">
        {/* 검색 입력 */}
        {onSearchChange && (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery || ''}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-40 pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {/* Refresh 버튼 */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        {/* 추가 액션 */}
        {actions}
      </div>
    </div>
  );
}
