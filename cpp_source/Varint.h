#pragma once

#include <cstdint>
#include <tuple>
#include "RawBuffer.h"


bool writeVarint( const uint64_t var, RawBuffer& buffer );

std::tuple<uint64_t, bool> readVarint( RawBuffer& buffer );

size_t sizeVarint( const uint64_t var );
