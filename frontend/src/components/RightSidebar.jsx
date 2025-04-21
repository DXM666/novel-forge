import React, { useState, useEffect } from 'react';

const RightSidebar = ({ visible, toggleRight, onStyleChange }) => {
  const [styles, setStyles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState(null);
  const [expandedIdx, setExpandedIdx] = useState(null);

  // 自动加载风格列表
  useEffect(() => {
    fetchStyles();
    // eslint-disable-next-line
  }, []);

  const fetchStyles = async () => {
    setLoading(true);
    setStyles([]);
    try {
      const res = await fetch('http://localhost:8000/api/styles/');
      const data = await res.json();
      setStyles(data.styles || []);
    } catch {
      setStyles([{ name: '获取失败', description: '请检查后端服务' }]);
    }
    setLoading(false);
  };

  const handleStyleSelect = (style, idx) => {
    setSelectedStyle(style);
    if (onStyleChange) onStyleChange(style);
    setExpandedIdx(idx === expandedIdx ? null : idx);
  };

  return (
    <div>
      <div id="rightSidebar" className={`sidebar-transition w-80 bg-white border-l border-gray-200 overflow-y-auto flex-shrink-0 ${visible ? '' : 'hidden'}`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">AI Writing Assistant</h2>
            <button onClick={toggleRight} className="text-gray-500 hover:text-gray-700">
              <i className={`fas ${visible ? 'fa-chevron-right' : 'fa-chevron-left'}`}></i>
            </button>
          </div>
          <div className="mt-4">
            <div className="mb-2">
              {loading && <span className="text-gray-500 text-sm">加载中...</span>}
            </div>
            {styles.length > 0 && (
              <ul className="bg-gray-50 rounded p-2 mt-2 max-h-60 overflow-y-auto text-sm">
                {styles.map((style, idx) => (
                  <li key={idx} className={`mb-1 rounded transition-all border ${selectedStyle && selectedStyle.name === style.name ? 'border-indigo-500 bg-white shadow' : 'border-transparent hover:bg-indigo-50'}`}
                      onClick={() => handleStyleSelect(style, idx)}
                      style={{ cursor: 'pointer', padding: '6px 8px' }}
                  >
                    <div className="flex items-center justify-between">
                      <b className={selectedStyle && selectedStyle.name === style.name ? 'text-indigo-700' : 'text-gray-900'}>{style.name}</b>
                      <button className="ml-2 text-xs text-indigo-400 hover:text-indigo-700 focus:outline-none" onClick={e => {e.stopPropagation(); setExpandedIdx(idx === expandedIdx ? null : idx);}}>
                        {expandedIdx === idx ? '收起' : '展开'}
                      </button>
                    </div>
                    <div className={`text-xs text-gray-600 mt-1 ${expandedIdx === idx ? '' : 'line-clamp-1 truncate'}`}>{style.description || '无描述'}</div>
                    {expandedIdx === idx && style.sample && (
                      <div className="mt-1 p-2 bg-indigo-50 rounded text-xs text-gray-700 border border-indigo-100">示例：{style.sample}</div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
      <div className="p-4">
        <div className="mb-6">
          <h3 className="font-medium text-gray-700 mb-3">Generate Content</h3>
          <div className="space-y-3">
            <button className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100">
              <span>Continue this passage</span>
              <i className="fas fa-chevron-right text-gray-400"></i>
            </button>
            <button className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100">
              <span>Improve this paragraph</span>
              <i className="fas fa-chevron-right text-gray-400"></i>
            </button>
            <button className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100">
              <span>Add dialogue</span>
              <i className="fas fa-chevron-right text-gray-400"></i>
            </button>
            <button className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100">
              <span>Describe a character</span>
              <i className="fas fa-chevron-right text-gray-400"></i>
            </button>
          </div>
        </div>
        <div className="mb-6">
          <h3 className="font-medium text-gray-700 mb-3">Writing Style</h3>
          <div className="grid grid-cols-2 gap-2">
            <button className="px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 text-sm">Descriptive</button>
            <button className="px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 text-sm">Concise</button>
            <button className="px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 text-sm">Poetic</button>
            <button className="px-3 py-2 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 text-sm">Suspenseful</button>
          </div>
          <div className="mt-3">
            <select className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm">
              <option>Mimic Author Style</option>
              <option>J.K. Rowling</option>
              <option>Stephen King</option>
              <option>Jane Austen</option>
              <option>Ernest Hemingway</option>
            </select>
          </div>
        </div>
        <div className="mb-6">
          <h3 className="font-medium text-gray-700 mb-3">Story Analysis</h3>
          <div className="bg-gray-50 rounded-md p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Pacing</span>
              <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">Good</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5 mb-3">
              <div className="bg-green-600 h-1.5 rounded-full" style={{ width: '65%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
};

export default RightSidebar;
