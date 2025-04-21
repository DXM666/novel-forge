import React, { useState } from 'react';

const RightSidebar = ({ visible, toggleRight }) => {
  const [styles, setStyles] = useState([]);
  const [loading, setLoading] = useState(false);

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
            <button
              className="w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-medium mb-2"
              onClick={fetchStyles}
              disabled={loading}
            >
              {loading ? '加载中...' : '获取风格列表'}
            </button>
            {styles.length > 0 && (
              <ul className="bg-gray-50 rounded p-2 mt-2 max-h-60 overflow-y-auto text-sm">
                {styles.map((style, idx) => (
                  <li key={idx} className="mb-1">
                    <b>{style.name}</b> - {style.description || '无描述'}
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
