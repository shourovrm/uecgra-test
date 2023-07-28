/*
 * ======================================================================
 * Mapper.h
 * ======================================================================
 * Mapper implementation header file.
 *
 * Author : Cheng Tan
 *   Date : July 16, 2019
 */

#include <llvm/IR/Function.h>
#include <llvm/IR/Value.h>
#include "DFG.h"
#include "CGRA.h"

using namespace llvm;

class Mapper {
  private:
//    typedef std::pair<Value*, StringRef> DFGNode;
//    typedef pair<DFGNode, DFGNode> DFGEdge;
    int m_maxMappingCycle;
    map<DFGNode*, CGRANode*> m_mapping;
    map<DFGNode*, int> m_mappingTiming;
    map<CGRANode*, int>* dijkstra_search(CGRA*, DFG*, int, DFGNode*,
        DFGNode*, CGRANode*);
    int getMaxMappingCycle();
    bool tryToRoute(CGRA*, DFG*, int, DFGNode*, CGRANode*, CGRANode*, bool, bool);
    list<DFGNode*>* getMappedDFGNodes(DFG*, CGRANode*);
    map<int, CGRANode*>* getReorderPath(map<CGRANode*, int>*);
    bool DFSMap(CGRA*, DFG*, int, list<DFGNode*>*, list<map<CGRANode*, int>*>*, bool);
    list<map<CGRANode*, int>*>* getOrderedPotentialPaths(CGRA*, DFG*, int,
        DFGNode*, list<map<CGRANode*, int>*>*);

  public:
    Mapper(){}
    int getResMII(DFG*, CGRA*);
    int getRecMII(DFG*);
    void constructMRRG(DFG*, CGRA*, int);
    bool heuristicMap(CGRA*, DFG*, int, bool);
    bool exhaustiveMap(CGRA*, DFG*, int, bool);
    map<CGRANode*, int>* calculateCost(CGRA*, DFG*, int, DFGNode*, CGRANode*);
    map<CGRANode*, int>* getPathWithMinCostAndConstraints(CGRA*, DFG*, int,
        DFGNode*, list<map<CGRANode*, int>*>*);
    bool schedule(CGRA*, DFG*, int, DFGNode*, map<CGRANode*, int>*, bool);
    void showSchedule(CGRA*, DFG*, int, bool);
    void writeJSON(CGRA*, DFG*, int, bool);
};
