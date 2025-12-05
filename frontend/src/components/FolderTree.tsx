import { useState } from 'react';
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react';
import clsx from 'clsx';
import type { FolderTreeNode } from '../types';

interface FolderTreeProps {
  nodes: FolderTreeNode[];
  onSelect?: (node: FolderTreeNode) => void;
  selectedPath?: string;
}

interface TreeNodeProps {
  node: FolderTreeNode;
  level: number;
  onSelect?: (node: FolderTreeNode) => void;
  selectedPath?: string;
}

function TreeNode({ node, level, onSelect, selectedPath }: TreeNodeProps) {
  const [isOpen, setIsOpen] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedPath === node.path;

  const handleClick = () => {
    if (hasChildren) {
      setIsOpen(!isOpen);
    }
    onSelect?.(node);
  };

  return (
    <div>
      <div
        className={clsx(
          'flex items-center py-1.5 px-2 cursor-pointer rounded-md transition-colors',
          isSelected ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100'
        )}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
      >
        {/* Expand/Collapse Icon */}
        <span className="w-5 h-5 flex items-center justify-center mr-1">
          {hasChildren ? (
            isOpen ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )
          ) : (
            <span className="w-4" />
          )}
        </span>

        {/* Folder Icon */}
        {isOpen ? (
          <FolderOpen className="w-5 h-5 text-yellow-500 mr-2" />
        ) : (
          <Folder className="w-5 h-5 text-yellow-500 mr-2" />
        )}

        {/* Folder Name */}
        <span className="flex-1 text-sm font-medium truncate">{node.name}</span>

        {/* Size */}
        <span className="text-xs text-gray-500 ml-2">{node.size_formatted}</span>
      </div>

      {/* Children */}
      {hasChildren && isOpen && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FolderTree({ nodes, onSelect, selectedPath }: FolderTreeProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden h-full flex flex-col">
      <div className="p-4 border-b border-gray-100 flex-shrink-0">
        <h3 className="font-semibold text-gray-900">Folder Structure</h3>
      </div>
      <div className="p-2 flex-1 overflow-y-auto">
        {nodes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No folders found. Run a scan to populate.
          </div>
        ) : (
          nodes.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              level={0}
              onSelect={onSelect}
              selectedPath={selectedPath}
            />
          ))
        )}
      </div>
    </div>
  );
}
