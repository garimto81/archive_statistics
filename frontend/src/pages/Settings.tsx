import { useState } from 'react';
import { Settings as SettingsIcon, FolderSync, Info } from 'lucide-react';
import clsx from 'clsx';
import FolderMapping from '../components/FolderMapping';

type SettingsTab = 'folder-mapping' | 'about';

export default function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('folder-mapping');

  const tabs = [
    { id: 'folder-mapping' as const, label: '폴더 매핑', icon: FolderSync },
    { id: 'about' as const, label: '정보', icon: Info },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-lg">
            <SettingsIcon className="w-6 h-6 text-gray-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-500">시스템 설정 및 관리</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 -mb-px transition-colors',
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'folder-mapping' && <FolderMapping />}
          {activeTab === 'about' && (
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Archive Statistics</h3>
                <dl className="space-y-3">
                  <div className="flex">
                    <dt className="w-32 text-gray-500">Version</dt>
                    <dd className="text-gray-900">1.14.0</dd>
                  </div>
                  <div className="flex">
                    <dt className="w-32 text-gray-500">Purpose</dt>
                    <dd className="text-gray-900">1PB NAS 아카이브 모니터링 대시보드</dd>
                  </div>
                  <div className="flex">
                    <dt className="w-32 text-gray-500">Stack</dt>
                    <dd className="text-gray-900">React + FastAPI + SQLite</dd>
                  </div>
                </dl>
              </div>

              <div className="bg-blue-50 rounded-lg p-6">
                <h3 className="text-lg font-medium text-blue-900 mb-2">폴더 매핑 기능</h3>
                <p className="text-blue-800 text-sm">
                  NAS 폴더와 Google Sheets의 WorkStatus를 명시적으로 연결하여 진행률을 정확하게 추적합니다.
                  기존 fuzzy matching 방식의 한계를 보완하고, 수동/자동 매칭을 모두 지원합니다.
                </p>
              </div>

              <div className="bg-yellow-50 rounded-lg p-6">
                <h3 className="text-lg font-medium text-yellow-900 mb-2">매칭 우선순위</h3>
                <ol className="text-yellow-800 text-sm list-decimal list-inside space-y-1">
                  <li><strong>FK 연결</strong> - 명시적으로 연결된 폴더 (가장 정확)</li>
                  <li><strong>Fuzzy Matching</strong> - 폴더명과 카테고리 자동 매칭 (fallback)</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
