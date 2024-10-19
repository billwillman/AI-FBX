#pragma once
#include <string>

using namespace std;

class FBXLoader
{
public:
	FBXLoader(const string& fileName);
	virtual ~FBXLoader();
};