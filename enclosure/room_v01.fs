FeatureScript 3095;
import(path : "onshape/std/common.fs", version : "3095.0");

function box(context is Context, id is Id, a is Vector, b is Vector) returns Query
{
    fCuboid(context, id, { "corner1" : a * millimeter, "corner2" : b * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function cylinder(context is Context, id is Id, x is number, y is number, z is number, h is number, diameter is number) returns Query
{
    fCylinder(context, id, { "bottomCenter" : vector(x,y,z)*millimeter,
        "topCenter" : vector(x,y,z+h)*millimeter, "radius" : diameter/2*millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function cut(context is Context, id is Id, target is Query, tool is Query)
{
    opBoolean(context, id, { "tools" : tool, "targets" : target, "operationType" : BooleanOperationType.SUBTRACTION });
}
function join(context is Context, id is Id, target is Query, tool is Query)
{
    opBoolean(context, id, { "tools" : qUnion([target,tool]), "operationType" : BooleanOperationType.UNION });
}
function namePart(context is Context, part is Query, title is string)
{
    setProperty(context, { "entities" : part, "propertyType" : PropertyType.NAME, "value" : title });
}
function roundedBox(context is Context, id is Id, a is Vector, b is Vector, radius is number) returns Query
{
    const part = box(context, id+"solid", a, b);
    var corners = [];
    for (var x in [a[0],b[0]])
        for (var y in [a[1],b[1]])
            corners = append(corners, qContainsPoint(qOwnedByBody(part,EntityType.EDGE), vector(x,y,(a[2]+b[2])/2)*millimeter));
    opFillet(context,id+"corners", { "entities" : qUnion(corners), "radius" : radius*millimeter });
    return part;
}
function insertBore(context is Context, id is Id, part is Query, x is number, y is number, top is number, diameter is number)
{
    cut(context,id+"cut",part,cylinder(context,id+"tool",x,y,top-4.5,5.5,diameter));
}

annotation { "Feature Type Name" : "Room V01 - Pico 2 W + SHT3x" }
export const roomV01 = defineFeature(function(context is Context, id is Id, definition is map)
precondition
{
    annotation { "Name" : "Insert bore diameter" }
    isLength(definition.insertDiameter, { (millimeter) : [3.0,3.1,3.4] } as LengthBoundSpec);
    annotation { "Name" : "Sensor PCB thickness (measure)" }
    isLength(definition.sensorThickness, { (millimeter) : [0.8,1.6,2.0] } as LengthBoundSpec);
    annotation { "Name" : "PCB side clearance" }
    isLength(definition.sensorClearance, { (millimeter) : [0.1,0.25,0.5] } as LengthBoundSpec);
}
{
    const bore = definition.insertDiameter / millimeter;
    const sensorTop = 7 + definition.sensorThickness / millimeter;
    const clearance = definition.sensorClearance / millimeter;
    // Print coordinates: shell open upwards; invert the assembled unit for shelf use.
    const shell = roundedBox(context,id+"shell",vector(0,0,0),vector(88,62,30),7);
    opFillet(context,id+"outerTop", {
        "entities" : qContainsPoint(qOwnedByBody(shell,EntityType.EDGE), vector(44,0,0)*millimeter),
        "radius" : 1.2*millimeter,
        "tangentPropagation" : true
    });
    const cavity = roundedBox(context,id+"cavity",vector(2.4,2.4,2.4),vector(85.6,59.6,31),4.6);
    cut(context,id+"hollow",shell,cavity);

    const caseMounts = [vector(7,7),vector(81,7),vector(7,55),vector(81,55)];
    for (var i=0; i<4; i+=1)
    {
        const p=caseMounts[i];
        const station=id+("caseMount"~i);
        join(context,station+"join",shell,cylinder(context,station+"boss",p[0],p[1],2,28,8));
        insertBore(context,station+"insert",shell,p[0],p[1],30,bore);
    }

    // Pico: 51 x 21 mm, hole spacing 47 x 11.4 mm, USB at x=4, antenna at x=55.
    const picoMounts = [vector(6,16.8),vector(6,28.2),vector(53,16.8),vector(53,28.2)];
    for (var i=0; i<4; i+=1)
    {
        const p=picoMounts[i];
        const station=id+("picoMount"~i);
        join(context,station+"join",shell,cylinder(context,station+"boss",p[0],p[1],2,6,5.3));
        insertBore(context,station+"insert",shell,p[0],p[1],8,bore);
    }
    // Oversized plug opening; verify against the actual microUSB cable moulding.
    const usb = box(context,id+"usbTool",vector(-1,15,5),vector(4.1,30,15));
    cut(context,id+"usbCut",shell,usb);

    // Thermal baffle stops short of the antenna side; a top notch routes jumpers.
    join(context,id+"baffleJoin",shell,box(context,id+"baffle",vector(2.3,38,2),vector(66,39.6,28)));
    cut(context,id+"wireNotchCut",shell,box(context,id+"wireNotch",vector(18,37,17),vector(30,40.6,31)));

    // The module slides into two edge rails; the removable keeper blocks the entrance.
    for (var side=0; side<2; side+=1)
    {
        const station=id+("sensorRail"~side);
        const x=side==0 ? 23.4-clearance : 37+clearance;
        join(context,station+"wallJoin",shell,box(context,station+"wall",vector(x,44,2),vector(x+1.6,57.4,sensorTop+1.8)));
        const a=side==0 ? x : 36;
        const b=side==0 ? 26 : x+1.6;
        join(context,station+"shelfJoin",shell,box(context,station+"shelf",vector(a,44,5.6),vector(b,56.3,7)));
        const lipA=side==0 ? x : 36.4;
        const lipB=side==0 ? 25.6 : x+1.6;
        join(context,station+"lipJoin",shell,box(context,station+"lip",vector(lipA,44,sensorTop+0.3),vector(lipB,57.4,sensorTop+1.8)));
    }
    join(context,id+"sensorStopJoin",shell,box(context,id+"sensorStop",vector(23,56.3,2),vector(39,57.5,sensorTop+1.8)));
    join(context,id+"keeperBossJoin",shell,cylinder(context,id+"keeperBoss",31,41,2,sensorTop-1.7,6));
    insertBore(context,id+"keeperInsert",shell,31,41,sensorTop+0.3,bore);

    // Narrow bridges print without internal support and expose the sensor bay to air.
    for (var i=0; i<10; i+=1)
    {
        const station=id+("vent"~i);
        const x=16+i*4.6;
        cut(context,station+"cut",shell,box(context,station+"tool",vector(x,59,7),vector(x+2.4,63,24)));
    }
    for (var i=0; i<4; i+=1)
    {
        const station=id+("rearVent"~i);
        cut(context,station+"cut",shell,box(context,station+"tool",vector(65+i*4, -1, 8),vector(67.4+i*4,3,20)));
    }
    namePart(context,shell,"ROOM V01 - shell 88 x 62 x 30 - PETG");

    // Bottom cover, external face on the bed. 1.5 mm remains under each screw head.
    const dx=100;
    const lid=roundedBox(context,id+"lid",vector(dx,0,0),vector(dx+88,62,4),7);
    opFillet(context,id+"lidOuterRim", {
        "entities" : qContainsPoint(qOwnedByBody(lid,EntityType.EDGE),vector(dx+44,0,0)*millimeter),
        "radius" : 1.0*millimeter, "tangentPropagation" : true
    });
    // Short locating tabs avoid the corner bosses and sensor rails.
    for (var y in [2.7,57.8])
        join(context,id+("tabJoin"~y),lid,box(context,id+("tab"~y),vector(dx+38,y,3.8),vector(dx+50,y+1.5,5.5)));
    for (var i=0; i<4; i+=1)
    {
        const p=caseMounts[i];
        const station=id+("lidScrew"~i);
        cut(context,station+"throughCut",lid,cylinder(context,station+"through",dx+p[0],p[1],-1,7,2.3));
        cut(context,station+"headCut",lid,cylinder(context,station+"head",dx+p[0],p[1],-1,3.5,3.8));
    }
    namePart(context,lid,"ROOM V01 - bottom cover - M2 x 4");

    const keeper=roundedBox(context,id+"keeper",vector(103,70,0),vector(111,77,1.5),1);
    cut(context,id+"keeperHoleCut",keeper,cylinder(context,id+"keeperHole",107,72.5,-1,4,2.3));
    namePart(context,keeper,"ROOM V01 - sensor keeper - M2 x 4");

    // Solid gauges detect obstructions in the board envelopes.
    const picoGauge=box(context,id+"picoGauge",vector(4.1,12.1,8.05),vector(54.9,32.9,8.95));
    const sensorGauge=box(context,id+"sensorGauge",vector(25.05,44.05,7.05),vector(36.95,55.95,sensorTop-0.05));
    const gauges=qUnion([picoGauge,sensorGauge]);
    if (size(evCollision(context,{"tools":gauges,"targets":shell}))!=0)
        throw "A mounting feature intersects a PCB envelope";
    opDeleteBodies(context,id+"deleteGauges",{"entities":gauges});
    for (var part in [shell,lid,keeper])
        if (size(evaluateQuery(context,part))!=1 || evVolume(context,{"entities":part})<=0*millimeter^3)
            throw "Each printed part must be one connected solid";
}, { "insertDiameter" : 3.1*millimeter, "sensorThickness" : 1.6*millimeter, "sensorClearance" : 0.25*millimeter });
