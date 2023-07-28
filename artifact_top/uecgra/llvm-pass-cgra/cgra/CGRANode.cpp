/*
 * ======================================================================
 * CGRANode.cpp
 * ======================================================================
 * CGRA tile implementation.
 *
 * Author : Cheng Tan
 *   Date : July 16, 2019
 */

#include "CGRANode.h"
#include <stdio.h>

//CGRANode::CGRANode(int t_id) {
//  m_id = t_id;
//  m_currentCtrlMemItems = 0;
//  m_canStore = false;
//  m_canLoad = false;
//}

CGRANode::CGRANode(int t_id, int t_x, int t_y) {
  m_id = t_id;
  m_currentCtrlMemItems = 0;
  m_canStore = false;
  m_canLoad = false;
  m_x = t_x;
  m_y = t_y;
  m_neighbors = NULL;
  m_occupiableInLinks = NULL;
  m_occupiableOutLinks = NULL;
  m_dfgNodes = new DFGNode*[1];
  m_fuOccupied = new bool[1];
  m_fuOccupied = new bool[1];

}

void CGRANode::setCtrlMemConstraint(int t_ctrlMemConstraint) {
  m_ctrlMemSize = t_ctrlMemConstraint;
}

void CGRANode::setRegConstraint(int t_registerConstraint) {
  m_registerCount = t_registerConstraint;
}

void CGRANode::setID(int t_id) {
  m_id = t_id;
}

void CGRANode::setLocation(int t_x, int t_y) {
  m_x = t_x;
  m_y = t_y;
}

int CGRANode::getID() {
  return m_id;
}

void CGRANode::attachInLink(CGRALink* t_link) {
  m_inLinks.push_back(t_link);
}

void CGRANode::attachOutLink(CGRALink* t_link) {
  m_outLinks.push_back(t_link);
}

list<CGRALink*>* CGRANode::getInLinks() {
  return &m_inLinks;
}

list<CGRALink*>* CGRANode::getOutLinks() {
  return &m_outLinks;
}

list<CGRANode*>* CGRANode::getNeighbors() {
  if (m_neighbors != NULL)
    return m_neighbors;
  m_neighbors = new list<CGRANode*>();
  for (CGRALink* link: m_outLinks)
    m_neighbors->push_back(link->getConnectedNode(this));
  return m_neighbors;
}

void CGRANode::constructMRRG(int t_CGRANodeCount, int t_II) {
  m_cycleBoundary = t_CGRANodeCount*t_II*t_II;
  // FIXME: Need to delete all these local arrays to avoid memory leakage.
  delete[] m_dfgNodes;
  m_dfgNodes = new DFGNode*[m_cycleBoundary];
  delete[] m_fuOccupied;
  m_fuOccupied = new bool[m_cycleBoundary];
  m_currentCtrlMemItems = 0;
  m_registers.clear();
  for (int i=0; i<m_cycleBoundary; ++i) {
    m_dfgNodes[i] = NULL;
    m_fuOccupied[i] = false;
  }
}

bool CGRANode::canOccupy(int t_cycle, int t_II) {
  // Check whether the limit of config mem is reached.
  if (m_currentCtrlMemItems + 1 > m_ctrlMemSize) {
    return false;
  }
  for (int cycle=t_cycle; cycle<m_cycleBoundary; cycle+=t_II) {
    if (m_fuOccupied[cycle]) {
      return false;
    }
  }
  return true;
}

bool CGRANode::canSupport(DFGNode* t_opt) {
  // Check whether this CGRA node supports the required functionality.
  if ((t_opt->isLoad() and !canLoad()) or
      (t_opt->isStore() and !canStore())){
    return false;
  }
  return true;
}

bool CGRANode::canOccupy(DFGNode* t_opt, int t_cycle, int t_II) {
  // Check whether this CGRA node supports the required functionality.
  if ((t_opt->isLoad() and !canLoad()) or (t_opt->isStore() and !canStore())){
    return false;
  }
  // Check whether the limit of config mem is reached.
  if (m_currentCtrlMemItems + 1 > m_ctrlMemSize) {
    return false;
  }
  for (int cycle=t_cycle; cycle<m_cycleBoundary; cycle+=t_II) {
    if (m_fuOccupied[cycle]) {
      return false;
    }
  }
  return true;
}

bool CGRANode::isOccupied(int t_cycle, int t_II) {
  for (int cycle=t_cycle; cycle<m_cycleBoundary; cycle+=t_II) {
    if (m_fuOccupied[cycle])
      return true;
  }
  return false;
}

void CGRANode::setDFGNode(DFGNode* t_opt, int t_cycle, int t_II,
    bool t_isStaticElasticCGRA) {
  int interval = t_II;
  if (t_isStaticElasticCGRA) {
    interval = 1;
  }
  for (int cycle=t_cycle; cycle<m_cycleBoundary; cycle+=interval) {
    assert(!m_fuOccupied[cycle]);
    m_dfgNodes[cycle] = t_opt;
    m_fuOccupied[cycle] = true;
  }
  ++m_currentCtrlMemItems;
  t_opt->setMapped();
}

DFGNode* CGRANode::getMappedDFGNode(int t_cycle) {
  if (m_dfgNodes[t_cycle] == NULL) {
    assert(0);
    return NULL;
  }
  return m_dfgNodes[t_cycle];
}

void CGRANode::configXbar(CGRALink*, int, int)
{

}

void CGRANode::addRegisterValue(float t_value) {
  m_registers.push_back(t_value);
}

list<CGRALink*>* CGRANode::getOccupiableInLinks(int t_cycle, int t_II) {
  if (m_occupiableInLinks == NULL)
    m_occupiableInLinks = new list<CGRALink*>();
  m_occupiableInLinks->clear();
  for (CGRALink* link: m_inLinks) {
    if (link->canOccupy(t_cycle, t_II)) {
      m_occupiableInLinks->push_back(link);
    }
  }
  return m_occupiableInLinks;
}

list<CGRALink*>* CGRANode::getOccupiableOutLinks(int t_cycle, int t_II) {
  if (m_occupiableOutLinks == NULL)
    m_occupiableOutLinks = new list<CGRALink*>();
  m_occupiableOutLinks->clear();
  for (CGRALink* link: m_outLinks) {
    if (link->canOccupy(t_cycle, t_II)) {
      m_occupiableOutLinks->push_back(link);
    }
  }
  return m_occupiableOutLinks;
}

int CGRANode::getAvailableRegisterCount() {
  return (m_registerCount - m_registers.size());
}

CGRALink* CGRANode::getInLink(CGRANode* t_node) {
  for (CGRALink* link: m_inLinks) {
    if (link->getSrc() == t_node) {
      return link;
    }
  }
  // will definitely return one inlink
  assert(0);
}

CGRALink* CGRANode::getOutLink(CGRANode* t_node) {
  for (CGRALink* link: m_outLinks) {
    if (link->getDst() == t_node)
      return link;
  }
  return NULL;
  // will definitely return one outlink
//  assert(0);
}

int CGRANode::getMinIdleCycle(int t_cycle, int t_II) {
  int tempCycle = t_cycle;
  while (tempCycle < m_cycleBoundary) {
    if (canOccupy(tempCycle, t_II))
      return tempCycle;
    ++tempCycle;
  }
  return m_cycleBoundary;
}

int CGRANode::getCurrentCtrlMemItems() {
  return m_currentCtrlMemItems;
}

void CGRANode::enableStore() {
  m_canStore = true;
}

void CGRANode::enableLoad() {
  m_canLoad = true;
}

bool CGRANode::canStore() {
  return m_canStore;
}

bool CGRANode::canLoad() {
  return m_canLoad;
}

int CGRANode::getX() {
  return m_x;
}

int CGRANode::getY() {
  return m_y;
}

