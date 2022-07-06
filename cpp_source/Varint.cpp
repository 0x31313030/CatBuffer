#include "Varint.h"

bool writeVarint( const uint64_t var, RawBuffer& buffer )
{
    void* ptr;

    if( var < 0xFD )
    {
        ptr = buffer.GetOffsetPtrAndMove(1); if(!ptr){ return false; }
        *((uint8_t*) ptr) = var;
    }
    else if( var < 0xFFFF )
    { 
        ptr = buffer.GetOffsetPtrAndMove(1); if(!ptr){ return false; }
        *((uint8_t*) ptr) = 0xFD;

        ptr = buffer.GetOffsetPtrAndMove(2); if(!ptr){ return false; }
        *((uint16_t*) ptr) = var;
    }
    else if( var < 0xFFFF'FFFF )
    {
        ptr = buffer.GetOffsetPtrAndMove(1); if(!ptr){ return false; }
        *((uint8_t*) ptr) = 0xFE;

        ptr = buffer.GetOffsetPtrAndMove(4); if(!ptr){ return false; }
        *((uint16_t*) ptr) = var;
    }
    else
    {
        ptr = buffer.GetOffsetPtrAndMove(1); if(!ptr){ return false; }
        *((uint8_t*) ptr) = 0xFF;

        ptr = buffer.GetOffsetPtrAndMove(8); if(!ptr){ return false; }
        *((uint64_t*) ptr) = var;
    }

    return true;
}

std::tuple<uint64_t, bool> readVarint( RawBuffer& buffer )
{
    uint64_t result { 0 };

    void* ptr { buffer.GetOffsetPtrAndMove(1) };
    if( !ptr )
    {
        return {0, false};
    }

    uint8_t  prefix { *((uint8_t*) ptr) };

    switch ( prefix )
    {
        case 0xFD: 
        {
            ptr    = buffer.GetOffsetPtrAndMove(2); if( !ptr ){ return {0, false}; }
            result = *((uint16_t*) ptr); 
            break; 
        }
        case 0xFE: 
        { 
            ptr    = buffer.GetOffsetPtrAndMove(4); if( !ptr ){ return {0, false}; }
            result = *((uint32_t*) ptr); 
            break; 
        }
        case 0xFF: 
        { 
            ptr    = buffer.GetOffsetPtrAndMove(8); if( !ptr ){ return {0, false}; }
            result = *((uint64_t*) ptr); 
            break; 
        }
        default:   
        {
            result = prefix;
            break;
        }
    }

    return {result, true};
}


size_t sizeVarint( const uint64_t var )
{
    if     ( var < 0xFD        ) { return 1; }
    else if( var < 0xFFFF      ) { return 3; }
    else if( var < 0xFFFF'FFFF ) { return 5; }
    else                         { return 9; }
}
